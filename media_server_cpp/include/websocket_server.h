#ifndef WEBSOCKET_SERVER_H
#define WEBSOCKET_SERVER_H

#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <string>
#include <memory>
#include <map>
#include <mutex>
#include <thread>
#include <functional>

namespace beast = boost::beast;
namespace websocket = beast::websocket;
namespace net = boost::asio;
using tcp = net::ip::tcp;

namespace onlylang {

class StreamingServer;

enum class MessageType {
    OFFER,
    ANSWER,
    ICE_CANDIDATE,
    JOIN,
    LEAVE,
    ERROR,
    VIEWER_JOINED,
    VIEWER_LEFT
};

struct WebSocketMessage {
    MessageType type;
    std::string data;
    std::string room_id;
    std::string peer_id;
};

class WebSocketSession : public std::enable_shared_from_this<WebSocketSession> {
public:
    WebSocketSession(tcp::socket socket, std::shared_ptr<StreamingServer> server);
    WebSocketSession(tcp::socket socket, std::shared_ptr<StreamingServer> server,
                     const std::string& room_id, const std::string& peer_id, bool is_host);
    ~WebSocketSession();

    void run();
    void run_already_upgraded();  // For pre-upgraded WebSocket connections
    void send(const std::string& message);
    void close();

    std::string get_room_id() const { return room_id_; }
    std::string get_peer_id() const { return peer_id_; }
    bool is_host() const { return is_host_; }

private:
    websocket::stream<tcp::socket> ws_;
    std::shared_ptr<StreamingServer> streaming_server_;
    beast::flat_buffer buffer_;
    std::string room_id_;
    std::string peer_id_;
    bool is_host_;
    std::mutex send_mutex_;

    void do_read();
    void on_read(beast::error_code ec, std::size_t bytes_transferred);
    void on_write(beast::error_code ec, std::size_t bytes_transferred);
    void handle_message(const std::string& message);
    WebSocketMessage parse_message(const std::string& json);
    std::string build_message(MessageType type, const std::string& data);
};

class WebSocketServer {
public:
    WebSocketServer(std::shared_ptr<StreamingServer> server,
                    const std::string& host, int port);
    ~WebSocketServer();

    bool start();
    void stop();

    void broadcast_to_room(const std::string& room_id, const std::string& message,
                          const std::string& exclude_peer_id = "");
    void send_to_peer(const std::string& peer_id, const std::string& message);

    void register_session(const std::string& peer_id,
                         std::shared_ptr<WebSocketSession> session);
    void unregister_session(const std::string& peer_id);

    // Accept an already-upgraded WebSocket connection from HTTP server
    void accept_upgraded_connection(int socket_fd, const std::string& room_id,
                                    const std::string& peer_id, bool is_host);

private:
    std::shared_ptr<StreamingServer> streaming_server_;
    std::string host_;
    int port_;
    net::io_context ioc_;
    tcp::acceptor acceptor_;
    std::thread accept_thread_;
    bool running_;

    std::map<std::string, std::shared_ptr<WebSocketSession>> sessions_;
    std::mutex sessions_mutex_;

    void do_accept();
    void on_accept(beast::error_code ec, tcp::socket socket);
};

} // namespace onlylang

#endif // WEBSOCKET_SERVER_H
