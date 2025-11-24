#include "websocket_server.h"
#include "streaming_server.h"
#include <iostream>
#include <sstream>

namespace onlylang {

// ============================================================================
// WebSocketSession Implementation
// ============================================================================

WebSocketSession::WebSocketSession(tcp::socket socket, std::shared_ptr<StreamingServer> server)
    : ws_(std::move(socket)),
      streaming_server_(server),
      is_host_(false) {
}

WebSocketSession::WebSocketSession(tcp::socket socket, std::shared_ptr<StreamingServer> server,
                                   const std::string& room_id, const std::string& peer_id, bool is_host)
    : ws_(std::move(socket)),
      streaming_server_(server),
      room_id_(room_id),
      peer_id_(peer_id),
      is_host_(is_host) {
}

WebSocketSession::~WebSocketSession() {
    close();
}

void WebSocketSession::run() {
    // Accept the WebSocket handshake
    ws_.async_accept(
        [self = shared_from_this()](beast::error_code ec) {
            if (ec) {
                std::cerr << "WebSocket accept error: " << ec.message() << std::endl;
                return;
            }

            std::cout << "🔌 WebSocket connection accepted" << std::endl;
            self->do_read();
        }
    );
}

void WebSocketSession::run_already_upgraded() {
    // Connection is already upgraded, skip handshake and start reading
    std::cout << "🔌 WebSocket connection from HTTP upgrade: room=" << room_id_
              << ", peer=" << peer_id_ << ", role=" << (is_host_ ? "host" : "viewer") << std::endl;
    do_read();
}

void WebSocketSession::send(const std::string& message) {
    std::lock_guard<std::mutex> lock(send_mutex_);

    try {
        ws_.write(net::buffer(message));
    } catch (const std::exception& e) {
        std::cerr << "WebSocket send error: " << e.what() << std::endl;
    }
}

void WebSocketSession::close() {
    try {
        if (ws_.is_open()) {
            ws_.close(websocket::close_code::normal);
        }
    } catch (const std::exception& e) {
        std::cerr << "WebSocket close error: " << e.what() << std::endl;
    }
}

void WebSocketSession::do_read() {
    ws_.async_read(
        buffer_,
        [self = shared_from_this()](beast::error_code ec, std::size_t bytes_transferred) {
            self->on_read(ec, bytes_transferred);
        }
    );
}

void WebSocketSession::on_read(beast::error_code ec, std::size_t bytes_transferred) {
    if (ec) {
        if (ec != websocket::error::closed) {
            std::cerr << "WebSocket read error: " << ec.message() << std::endl;
        }
        return;
    }

    // Convert buffer to string
    std::string message = beast::buffers_to_string(buffer_.data());
    buffer_.consume(buffer_.size());

    std::cout << "📨 WebSocket message received: " << message << std::endl;

    // Handle the message
    handle_message(message);

    // Continue reading
    do_read();
}

void WebSocketSession::on_write(beast::error_code ec, std::size_t bytes_transferred) {
    if (ec) {
        std::cerr << "WebSocket write error: " << ec.message() << std::endl;
    }
}

void WebSocketSession::handle_message(const std::string& message) {
    WebSocketMessage msg = parse_message(message);

    switch (msg.type) {
        case MessageType::JOIN: {
            // Extract room_id from data
            // Expected format: {"room_id":"room_123","user_id":"user_456","role":"host"}
            room_id_ = msg.room_id;

            // Determine if host or viewer
            is_host_ = (msg.data.find("\"role\":\"host\"") != std::string::npos);

            // Add peer to streaming server
            ParticipantRole role = is_host_ ? ParticipantRole::HOST : ParticipantRole::VIEWER;
            peer_id_ = streaming_server_->add_peer(room_id_, msg.data, msg.data, role);

            std::cout << "👤 Peer joined: " << peer_id_
                     << " in room: " << room_id_
                     << " as " << (is_host_ ? "HOST" : "VIEWER") << std::endl;

            // Send acknowledgment
            std::string ack = build_message(MessageType::JOIN,
                "{\"peer_id\":\"" + peer_id_ + "\",\"room_id\":\"" + room_id_ + "\"}");
            send(ack);
            break;
        }

        case MessageType::OFFER: {
            // Handle SDP offer from host
            std::cout << "📤 Received SDP offer from: " << peer_id_ << std::endl;

            // Process through streaming server
            // The offer will be forwarded to all viewers in the room
            // For now, just acknowledge
            std::string response = build_message(MessageType::ANSWER, msg.data);
            send(response);
            break;
        }

        case MessageType::ANSWER: {
            // Handle SDP answer from viewer
            std::cout << "📥 Received SDP answer from: " << peer_id_ << std::endl;
            break;
        }

        case MessageType::ICE_CANDIDATE: {
            // Handle ICE candidate
            std::cout << "🧊 Received ICE candidate from: " << peer_id_ << std::endl;
            // Forward ICE candidate through streaming server
            break;
        }

        case MessageType::LEAVE: {
            // Handle peer leaving
            std::cout << "👋 Peer leaving: " << peer_id_ << std::endl;
            if (!peer_id_.empty()) {
                streaming_server_->remove_peer(peer_id_);
            }
            close();
            break;
        }

        default:
            std::cerr << "Unknown message type" << std::endl;
            break;
    }
}

WebSocketMessage WebSocketSession::parse_message(const std::string& json) {
    WebSocketMessage msg;
    msg.data = json;

    // Simple JSON parsing (in production, use a proper JSON library)
    if (json.find("\"type\":\"join\"") != std::string::npos ||
        json.find("\"type\":\"JOIN\"") != std::string::npos) {
        msg.type = MessageType::JOIN;

        // Extract room_id
        size_t room_pos = json.find("\"room_id\":\"");
        if (room_pos != std::string::npos) {
            size_t start = room_pos + 11;
            size_t end = json.find("\"", start);
            if (end != std::string::npos) {
                msg.room_id = json.substr(start, end - start);
            }
        }
    }
    else if (json.find("\"type\":\"offer\"") != std::string::npos) {
        msg.type = MessageType::OFFER;
    }
    else if (json.find("\"type\":\"answer\"") != std::string::npos) {
        msg.type = MessageType::ANSWER;
    }
    else if (json.find("\"type\":\"ice_candidate\"") != std::string::npos ||
             json.find("\"type\":\"candidate\"") != std::string::npos) {
        msg.type = MessageType::ICE_CANDIDATE;
    }
    else if (json.find("\"type\":\"leave\"") != std::string::npos) {
        msg.type = MessageType::LEAVE;
    }
    else {
        msg.type = MessageType::ERROR;
    }

    return msg;
}

std::string WebSocketSession::build_message(MessageType type, const std::string& data) {
    std::ostringstream oss;
    oss << "{\"type\":\"";

    switch (type) {
        case MessageType::OFFER:
            oss << "offer";
            break;
        case MessageType::ANSWER:
            oss << "answer";
            break;
        case MessageType::ICE_CANDIDATE:
            oss << "ice_candidate";
            break;
        case MessageType::JOIN:
            oss << "join";
            break;
        case MessageType::LEAVE:
            oss << "leave";
            break;
        case MessageType::VIEWER_JOINED:
            oss << "viewer_joined";
            break;
        case MessageType::VIEWER_LEFT:
            oss << "viewer_left";
            break;
        case MessageType::ERROR:
            oss << "error";
            break;
    }

    oss << "\",\"data\":" << data << "}";
    return oss.str();
}

// ============================================================================
// WebSocketServer Implementation
// ============================================================================

WebSocketServer::WebSocketServer(std::shared_ptr<StreamingServer> server,
                                 const std::string& host, int port)
    : streaming_server_(server),
      host_(host),
      port_(port),
      acceptor_(ioc_),
      running_(false) {
}

WebSocketServer::~WebSocketServer() {
    stop();
}

bool WebSocketServer::start() {
    if (running_) {
        return true;
    }

    try {
        auto const address = net::ip::make_address(host_);
        tcp::endpoint endpoint{address, static_cast<unsigned short>(port_)};

        acceptor_.open(endpoint.protocol());
        acceptor_.set_option(net::socket_base::reuse_address(true));
        acceptor_.bind(endpoint);
        acceptor_.listen(net::socket_base::max_listen_connections);

        running_ = true;

        // Start accepting connections in a separate thread
        accept_thread_ = std::thread([this]() {
            do_accept();
            ioc_.run();
        });

        std::cout << "WebSocket server listening on " << host_ << ":" << port_ << std::endl;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Failed to start WebSocket server: " << e.what() << std::endl;
        return false;
    }
}

void WebSocketServer::stop() {
    if (!running_) {
        return;
    }

    running_ = false;

    // Close all sessions
    {
        std::lock_guard<std::mutex> lock(sessions_mutex_);
        for (auto& [peer_id, session] : sessions_) {
            session->close();
        }
        sessions_.clear();
    }

    // Stop accepting new connections
    if (acceptor_.is_open()) {
        acceptor_.close();
    }

    // Stop io_context
    ioc_.stop();

    // Wait for accept thread to finish
    if (accept_thread_.joinable()) {
        accept_thread_.join();
    }

    std::cout << "WebSocket server stopped" << std::endl;
}

void WebSocketServer::do_accept() {
    acceptor_.async_accept(
        [this](beast::error_code ec, tcp::socket socket) {
            on_accept(ec, std::move(socket));
        }
    );
}

void WebSocketServer::on_accept(beast::error_code ec, tcp::socket socket) {
    if (ec) {
        std::cerr << "WebSocket accept error: " << ec.message() << std::endl;
    } else {
        // Create new session
        auto session = std::make_shared<WebSocketSession>(std::move(socket), streaming_server_);
        session->run();
    }

    // Continue accepting
    if (running_) {
        do_accept();
    }
}

void WebSocketServer::broadcast_to_room(const std::string& room_id, const std::string& message,
                                       const std::string& exclude_peer_id) {
    std::lock_guard<std::mutex> lock(sessions_mutex_);

    for (const auto& [peer_id, session] : sessions_) {
        if (session->get_room_id() == room_id && peer_id != exclude_peer_id) {
            session->send(message);
        }
    }
}

void WebSocketServer::send_to_peer(const std::string& peer_id, const std::string& message) {
    std::lock_guard<std::mutex> lock(sessions_mutex_);

    auto it = sessions_.find(peer_id);
    if (it != sessions_.end()) {
        it->second->send(message);
    }
}

void WebSocketServer::register_session(const std::string& peer_id,
                                       std::shared_ptr<WebSocketSession> session) {
    std::lock_guard<std::mutex> lock(sessions_mutex_);
    sessions_[peer_id] = session;
}

void WebSocketServer::unregister_session(const std::string& peer_id) {
    std::lock_guard<std::mutex> lock(sessions_mutex_);
    sessions_.erase(peer_id);
}

void WebSocketServer::accept_upgraded_connection(int socket_fd, const std::string& room_id,
                                                  const std::string& peer_id, bool is_host) {
    try {
        // Create a Boost.Asio socket from the file descriptor
        tcp::socket socket(ioc_);
        socket.assign(tcp::v4(), socket_fd);

        // Create a WebSocket session with the pre-set room_id and peer_id
        auto session = std::make_shared<WebSocketSession>(
            std::move(socket), streaming_server_, room_id, peer_id, is_host
        );

        // Register the session
        register_session(peer_id, session);

        // Start reading (skip the handshake as it's already done)
        session->run_already_upgraded();

        std::cout << "✅ Accepted upgraded WebSocket connection for peer: " << peer_id
                  << " in room: " << room_id << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Failed to accept upgraded connection: " << e.what() << std::endl;
    }
}

} // namespace onlylang
