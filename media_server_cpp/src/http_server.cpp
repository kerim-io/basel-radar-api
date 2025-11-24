#include "http_server.h"
#include "room_manager.h"
#include "streaming_server.h"
#include "websocket_server.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cerrno>
#include <iostream>
#include <sstream>
#include <cstring>
#include <vector>
#include <iomanip>
#include <algorithm>
#include <chrono>
#include <openssl/sha.h>
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/buffer.h>

namespace onlylang {

HttpServer::HttpServer(const std::string& host, int port,
                       std::shared_ptr<RoomManager> room_manager,
                       std::shared_ptr<StreamingServer> streaming_server)
    : host_(host),
      port_(port),
      running_(false),
      room_manager_(room_manager),
      streaming_server_(streaming_server),
      server_socket_(-1) {
}

HttpServer::~HttpServer() {
    stop();
}

bool HttpServer::start() {
    if (running_) {
        return true;
    }

    server_socket_ = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket_ < 0) {
        std::cerr << "Failed to create socket" << std::endl;
        return false;
    }

    int opt = 1;
    if (setsockopt(server_socket_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        std::cerr << "Failed to set socket options" << std::endl;
        close(server_socket_);
        return false;
    }

    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port_);

    if (bind(server_socket_, (struct sockaddr*)&address, sizeof(address)) < 0) {
        std::cerr << "Failed to bind socket to port " << port_ << std::endl;
        close(server_socket_);
        return false;
    }

    if (listen(server_socket_, 10) < 0) {
        std::cerr << "Failed to listen on socket" << std::endl;
        close(server_socket_);
        return false;
    }

    setup_routes();
    running_ = true;

    accept_thread_ = std::thread(&HttpServer::accept_connections, this);

    std::cout << "HTTP server listening on " << host_ << ":" << port_ << std::endl;
    return true;
}

void HttpServer::stop() {
    if (!running_) {
        return;
    }

    running_ = false;

    if (server_socket_ >= 0) {
        close(server_socket_);
        server_socket_ = -1;
    }

    if (accept_thread_.joinable()) {
        accept_thread_.join();
    }

    std::cout << "HTTP server stopped" << std::endl;
}

void HttpServer::register_route(const std::string& method, const std::string& path, RouteHandler handler) {
    routes_[method][path] = handler;
}

void HttpServer::setup_routes() {
    register_route("POST", "/room/create", [this](const HttpRequest& req) {
        return handle_create_room(req);
    });

    register_route("POST", "/room/:room_id/stop", [this](const HttpRequest& req) {
        return handle_delete_room(req);
    });

    register_route("GET", "/room/:room_id/stats", [this](const HttpRequest& req) {
        return handle_get_room_stats(req);
    });

    register_route("GET", "/stats", [this](const HttpRequest& req) {
        return handle_get_server_stats(req);
    });

    register_route("GET", "/health", [this](const HttpRequest& req) {
        return handle_health_check(req);
    });
}

void HttpServer::accept_connections() {
    while (running_) {
        struct sockaddr_in client_address;
        socklen_t client_len = sizeof(client_address);

        int client_socket = accept(server_socket_, (struct sockaddr*)&client_address, &client_len);

        if (client_socket < 0) {
            if (running_) {
                std::cerr << "Failed to accept connection" << std::endl;
            }
            continue;
        }

        std::thread(&HttpServer::handle_client, this, client_socket).detach();
    }
}

void HttpServer::handle_client(int client_socket) {
    try {
        // Set socket timeout to prevent slowloris attacks
        struct timeval tv;
        tv.tv_sec = 30;  // 30 second timeout
        tv.tv_usec = 0;
        setsockopt(client_socket, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

        constexpr size_t MAX_REQUEST_SIZE = 16384;
        std::string raw_request;
        std::vector<char> buffer(MAX_REQUEST_SIZE);

        // Read all available data (headers + body)
        ssize_t total_bytes = 0;
        while (true) {
            ssize_t bytes_read = read(client_socket, buffer.data(), buffer.size());

            if (bytes_read < 0) {
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    break;  // No more data available
                }
                std::cerr << "Error reading from socket: " << strerror(errno) << std::endl;
                close(client_socket);
                return;
            }

            if (bytes_read == 0) {
                break;  // Connection closed
            }

            raw_request.append(buffer.data(), bytes_read);
            total_bytes += bytes_read;

            // Check if we have complete request (headers + body)
            size_t header_end = raw_request.find("\r\n\r\n");
            if (header_end != std::string::npos) {
                // Found end of headers, check if we have full body
                std::string headers = raw_request.substr(0, header_end);
                size_t content_length = 0;

                // Extract Content-Length
                size_t cl_pos = headers.find("Content-Length:");
                if (cl_pos == std::string::npos) {
                    cl_pos = headers.find("content-length:");
                }
                if (cl_pos != std::string::npos) {
                    size_t value_start = cl_pos + 15;  // length of "Content-Length:"
                    while (value_start < headers.length() &&
                           (headers[value_start] == ' ' || headers[value_start] == '\t')) {
                        value_start++;
                    }
                    size_t value_end = headers.find('\r', value_start);
                    if (value_end != std::string::npos) {
                        std::string cl_str = headers.substr(value_start, value_end - value_start);
                        content_length = std::stoul(cl_str);
                    }
                }

                size_t body_start = header_end + 4;  // Skip "\r\n\r\n"
                size_t current_body_length = raw_request.length() - body_start;

                if (current_body_length >= content_length) {
                    // We have the complete request
                    break;
                }
            }

            // Prevent infinite loops and DoS
            if (total_bytes >= MAX_REQUEST_SIZE) {
                break;
            }
        }

        if (raw_request.empty()) {
            close(client_socket);
            return;
        }

        HttpRequest request = parse_request(raw_request);

        // Check if this is a WebSocket upgrade request
        if (is_websocket_upgrade(request)) {
            if (handle_websocket_upgrade(client_socket, request)) {
                // WebSocket connection established, don't close the socket
                return;
            }
            // If upgrade failed, close the socket
            close(client_socket);
            return;
        }

        RouteHandler handler;
        std::map<std::string, std::string> params;

        HttpResponse response;

        if (match_route(request.method, request.path, handler, params)) {
            request.path_params = params;
            response = handler(request);
        } else {
            response.status_code = 404;
            response.set_error(404, "Route not found");
        }

        std::string response_str = build_response(response);
        ssize_t bytes_written = write(client_socket, response_str.c_str(), response_str.length());

        if (bytes_written < 0) {
            std::cerr << "Error writing to socket: " << strerror(errno) << std::endl;
        }

        close(client_socket);
    } catch (const std::exception& e) {
        std::cerr << "Exception in handle_client: " << e.what() << std::endl;
        close(client_socket);
    } catch (...) {
        std::cerr << "Unknown exception in handle_client" << std::endl;
        close(client_socket);
    }
}

HttpRequest HttpServer::parse_request(const std::string& raw_request) {
    HttpRequest request;

    std::istringstream stream(raw_request);
    std::string line;

    if (std::getline(stream, line)) {
        std::istringstream line_stream(line);
        std::string path_query;
        line_stream >> request.method >> path_query;

        size_t query_pos = path_query.find('?');
        if (query_pos != std::string::npos) {
            request.path = path_query.substr(0, query_pos);
            std::string query = path_query.substr(query_pos + 1);
        } else {
            request.path = path_query;
        }
    }

    while (std::getline(stream, line) && line != "\r") {
        size_t colon_pos = line.find(':');
        if (colon_pos != std::string::npos && colon_pos + 2 < line.length()) {
            std::string key = line.substr(0, colon_pos);
            std::string value = line.substr(colon_pos + 2);
            if (!value.empty() && value.back() == '\r') {
                value.pop_back();
            }
            request.headers[key] = value;
        }
    }

    std::string remaining;
    while (std::getline(stream, line)) {
        remaining += line + "\n";
    }
    request.body = remaining;

    return request;
}

std::string HttpServer::build_response(const HttpResponse& response) {
    std::ostringstream oss;

    oss << "HTTP/1.1 " << response.status_code << " ";

    switch (response.status_code) {
        case 200: oss << "OK"; break;
        case 201: oss << "Created"; break;
        case 400: oss << "Bad Request"; break;
        case 404: oss << "Not Found"; break;
        case 500: oss << "Internal Server Error"; break;
        default: oss << "Unknown"; break;
    }

    oss << "\r\n";

    for (const auto& [key, value] : response.headers) {
        oss << key << ": " << value << "\r\n";
    }

    oss << "Content-Length: " << response.body.length() << "\r\n";
    oss << "Connection: close\r\n";
    oss << "\r\n";
    oss << response.body;

    return oss.str();
}

bool HttpServer::match_route(const std::string& method, const std::string& path,
                             RouteHandler& handler, std::map<std::string, std::string>& params) {
    auto method_routes = routes_.find(method);
    if (method_routes == routes_.end()) {
        return false;
    }

    // FIRST PASS: Check exact routes (no parameters)
    for (const auto& [pattern, route_handler] : method_routes->second) {
        if (pattern.find(':') == std::string::npos) {
            if (pattern == path) {
                handler = route_handler;
                return true;
            }
        }
    }

    // SECOND PASS: Check parametrized routes
    for (const auto& [pattern, route_handler] : method_routes->second) {
        if (pattern.find(':') != std::string::npos) {
            // Clear params for this attempt
            params.clear();

            std::istringstream pattern_stream(pattern);
            std::istringstream path_stream(path);
            std::string pattern_part, path_part;
            bool match = true;

            while (std::getline(pattern_stream, pattern_part, '/') &&
                   std::getline(path_stream, path_part, '/')) {
                if (pattern_part.empty() && path_part.empty()) continue;

                if (!pattern_part.empty() && pattern_part[0] == ':') {
                    std::string param_name = pattern_part.substr(1);
                    params[param_name] = path_part;
                } else if (pattern_part != path_part) {
                    match = false;
                    break;
                }
            }

            // Both streams must be exhausted for a match
            if (match && !std::getline(pattern_stream, pattern_part, '/') &&
                !std::getline(path_stream, path_part, '/')) {
                handler = route_handler;
                return true;
            }
        }
    }

    return false;
}

HttpResponse HttpServer::handle_create_room(const HttpRequest& req) {
    HttpResponse response;

    // Debug logging
    std::cout << "=== CREATE ROOM REQUEST ===" << std::endl;
    std::cout << "Body length: " << req.body.length() << std::endl;
    std::cout << "Body: [" << req.body << "]" << std::endl;
    std::cout << "=========================" << std::endl;

    std::string post_id;
    std::string host_user_id;

    // Parse post_id (handle both "post_id":"value" and "post_id": "value")
    size_t post_pos = req.body.find("\"post_id\"");
    if (post_pos != std::string::npos) {
        size_t colon_pos = req.body.find(":", post_pos);
        if (colon_pos != std::string::npos) {
            size_t quote_start = req.body.find("\"", colon_pos);
            if (quote_start != std::string::npos) {
                size_t start = quote_start + 1;
                if (start < req.body.length()) {
                    size_t end = req.body.find("\"", start);
                    if (end != std::string::npos && end > start) {
                        post_id = req.body.substr(start, end - start);
                        if (post_id.length() > 256) {
                            response.set_error(400, "post_id too long");
                            return response;
                        }
                    }
                }
            }
        }
    }

    // Parse host_user_id (handle both "host_user_id":"value" and "host_user_id": "value")
    size_t host_pos = req.body.find("\"host_user_id\"");
    if (host_pos != std::string::npos) {
        size_t colon_pos = req.body.find(":", host_pos);
        if (colon_pos != std::string::npos) {
            size_t quote_start = req.body.find("\"", colon_pos);
            if (quote_start != std::string::npos) {
                size_t start = quote_start + 1;
                if (start < req.body.length()) {
                    size_t end = req.body.find("\"", start);
                    if (end != std::string::npos && end > start) {
                        host_user_id = req.body.substr(start, end - start);
                        if (host_user_id.length() > 256) {
                            response.set_error(400, "host_user_id too long");
                            return response;
                        }
                    }
                }
            }
        }
    }

    if (post_id.empty() || host_user_id.empty()) {
        response.set_error(400, "Missing post_id or host_user_id");
        return response;
    }

    std::string room_id = streaming_server_->create_room(post_id, host_user_id);

    if (room_id.empty()) {
        response.set_error(500, "Failed to create room");
        return response;
    }

    response.status_code = 201;
    response.set_json("{\"room_id\":\"" + room_id + "\",\"post_id\":\"" + post_id + "\"}");
    return response;
}

HttpResponse HttpServer::handle_delete_room(const HttpRequest& req) {
    HttpResponse response;

    auto it = req.path_params.find("room_id");
    if (it == req.path_params.end()) {
        response.set_error(400, "Missing room_id parameter");
        return response;
    }

    std::string room_id = it->second;

    if (!streaming_server_->delete_room(room_id)) {
        response.set_error(404, "Room not found");
        return response;
    }

    response.set_json("{\"status\":\"stopped\",\"room_id\":\"" + room_id + "\"}");
    return response;
}

HttpResponse HttpServer::handle_get_room_stats(const HttpRequest& req) {
    HttpResponse response;

    auto it = req.path_params.find("room_id");
    if (it == req.path_params.end()) {
        response.set_error(400, "Missing room_id parameter");
        return response;
    }

    std::string room_id = it->second;
    Room* room = streaming_server_->get_room(room_id);

    if (!room) {
        response.set_error(404, "Room not found");
        return response;
    }

    std::ostringstream json;
    json << "{";
    json << "\"room_id\":\"" << room->room_id << "\",";
    json << "\"post_id\":\"" << room->post_id << "\",";
    json << "\"is_active\":" << (room->is_active ? "true" : "false") << ",";
    json << "\"viewer_count\":" << room->viewer_count() << ",";
    json << "\"has_host\":" << (room->has_host() ? "true" : "false");
    json << "}";

    response.set_json(json.str());
    return response;
}

HttpResponse HttpServer::handle_get_server_stats(const HttpRequest& req) {
    HttpResponse response;

    auto stats = streaming_server_->get_stats();

    std::ostringstream json;
    json << "{";
    json << "\"total_rooms\":" << stats.total_rooms << ",";
    json << "\"active_rooms\":" << stats.active_rooms << ",";
    json << "\"total_peers\":" << stats.total_peers << ",";
    json << "\"total_viewers\":" << stats.total_viewers << ",";
    json << "\"total_hosts\":" << stats.total_hosts << ",";
    json << "\"total_bytes_sent\":" << stats.total_bytes_sent << ",";
    json << "\"total_bytes_received\":" << stats.total_bytes_received;
    json << "}";

    response.set_json(json.str());
    return response;
}

HttpResponse HttpServer::handle_health_check(const HttpRequest& req) {
    HttpResponse response;
    response.set_json("{\"status\":\"healthy\",\"service\":\"media_server\"}");
    return response;
}

bool HttpServer::is_websocket_upgrade(const HttpRequest& req) {
    // Check for WebSocket upgrade headers
    auto upgrade_it = req.headers.find("Upgrade");
    auto connection_it = req.headers.find("Connection");
    auto ws_key_it = req.headers.find("Sec-WebSocket-Key");

    if (upgrade_it == req.headers.end() || connection_it == req.headers.end() || ws_key_it == req.headers.end()) {
        return false;
    }

    // Case-insensitive comparison for "websocket"
    std::string upgrade_val = upgrade_it->second;
    std::transform(upgrade_val.begin(), upgrade_val.end(), upgrade_val.begin(), ::tolower);

    return upgrade_val.find("websocket") != std::string::npos;
}

std::string HttpServer::compute_websocket_accept(const std::string& key) {
    // WebSocket protocol magic string
    const std::string magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
    std::string input = key + magic;

    // Compute SHA-1 hash
    unsigned char hash[SHA_DIGEST_LENGTH];
    SHA1(reinterpret_cast<const unsigned char*>(input.c_str()), input.length(), hash);

    // Base64 encode
    BIO *bio, *b64;
    BUF_MEM *buffer_ptr;

    b64 = BIO_new(BIO_f_base64());
    bio = BIO_new(BIO_s_mem());
    bio = BIO_push(b64, bio);

    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL);
    BIO_write(bio, hash, SHA_DIGEST_LENGTH);
    BIO_flush(bio);
    BIO_get_mem_ptr(bio, &buffer_ptr);

    std::string result(buffer_ptr->data, buffer_ptr->length);
    BIO_free_all(bio);

    return result;
}

bool HttpServer::handle_websocket_upgrade(int client_socket, const HttpRequest& req) {
    std::cout << "=== WebSocket Upgrade Request ===" << std::endl;
    std::cout << "Path: " << req.path << std::endl;

    if (!websocket_server_) {
        std::cerr << "WebSocket server not available" << std::endl;
        return false;
    }

    // Extract room_id from path (e.g., /room/123/host or /room/123/viewer)
    std::string room_id;
    bool is_host = false;

    // Parse path: /room/:room_id/:role
    size_t room_pos = req.path.find("/room/");
    if (room_pos != std::string::npos) {
        size_t id_start = room_pos + 6;  // length of "/room/"
        size_t id_end = req.path.find("/", id_start);

        if (id_end != std::string::npos) {
            room_id = req.path.substr(id_start, id_end - id_start);
            std::string role = req.path.substr(id_end + 1);

            if (role == "host") {
                is_host = true;
            } else if (role == "viewer") {
                is_host = false;
            } else {
                std::cerr << "Invalid role: " << role << std::endl;
                return false;
            }
        }
    }

    if (room_id.empty()) {
        std::cerr << "Could not extract room_id from path: " << req.path << std::endl;
        return false;
    }

    std::cout << "Room ID: " << room_id << ", Role: " << (is_host ? "host" : "viewer") << std::endl;

    // Get Sec-WebSocket-Key
    auto key_it = req.headers.find("Sec-WebSocket-Key");
    if (key_it == req.headers.end()) {
        std::cerr << "Missing Sec-WebSocket-Key header" << std::endl;
        return false;
    }

    std::string accept_key = compute_websocket_accept(key_it->second);

    // Send WebSocket handshake response
    std::ostringstream response;
    response << "HTTP/1.1 101 Switching Protocols\r\n";
    response << "Upgrade: websocket\r\n";
    response << "Connection: Upgrade\r\n";
    response << "Sec-WebSocket-Accept: " << accept_key << "\r\n";
    response << "\r\n";

    std::string response_str = response.str();
    ssize_t bytes_written = write(client_socket, response_str.c_str(), response_str.length());

    if (bytes_written < 0) {
        std::cerr << "Failed to send WebSocket handshake response" << std::endl;
        return false;
    }

    std::cout << "WebSocket handshake complete, transferring to WebSocket server" << std::endl;

    // Generate peer_id
    std::string peer_id = room_id + "_" + (is_host ? "host" : "viewer") + "_" +
                          std::to_string(std::chrono::system_clock::now().time_since_epoch().count());

    // Transfer the socket to the WebSocket server
    websocket_server_->accept_upgraded_connection(client_socket, room_id, peer_id, is_host);

    return true;
}

} // namespace onlylang