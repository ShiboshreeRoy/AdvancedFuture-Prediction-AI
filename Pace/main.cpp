#include <iostream>
#include <chrono>
#include <thread>
#include <random>
#include <string>
#include <sstream>
#include <iomanip>
#include <nlohmann/json.hpp> // include this header-only JSON lib (add to project)
#include <mqtt/async_client.h> // e.g., Eclipse Paho C++ library

using json = nlohmann::json;

std::string iso8601_now() {
    auto now = std::chrono::system_clock::now();
    std::time_t t = std::chrono::system_clock::to_time_t(now);
    std::tm tm = *std::gmtime(&t);
    std::ostringstream ss;
    ss << std::put_time(&tm, "%FT%TZ");
    return ss.str();
}

int main(int argc, char** argv) {
    // Config
    const std::string SERVER_URI = "ssl://mqtt.example.com:8883";
    const std::string CLIENT_ID = "hr-sim-001";
    const std::string TOPIC = "devices/hr_sim/telemetry";
    const int QOS = 1;
    const int PUBLISH_INTERVAL_MS = 1000;

    // RNG for simulated HR
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<> hr_dist(72.0, 5.0); // mean 72 bpm, sd 5

    // MQTT client setup (Paho)
    mqtt::async_client client(SERVER_URI, CLIENT_ID);

    mqtt::connect_options connOpts;
    connOpts.set_clean_session(true);

    // TLS options (example: set paths or use in-memory certs)
    mqtt::ssl_options sslOpts;
    sslOpts.set_trust_store("ca.pem");          // CA cert file
    sslOpts.set_key_store("client.pem");       // client cert (if used)
    sslOpts.set_private_key("client.key");     // client private key (if used)
    connOpts.set_ssl(sslOpts);

    try {
        std::cout << "Connecting to MQTT broker..." << std::endl;
        auto tok = client.connect(connOpts);
        tok->wait();
        std::cout << "Connected." << std::endl;

        for (;;) {
            double hr = hr_dist(gen);
            if (hr < 40) hr = 40; // clamp
            if (hr > 180) hr = 180;

            json payload = {
                {"timestamp", iso8601_now()},
                {"simulated_hr_bpm", std::round(hr)}
            };

            std::string msg = payload.dump();
            auto pubtok = client.publish(TOPIC, msg.c_str(), (int)msg.size(), QOS, false);
            pubtok->wait_for(std::chrono::seconds(2));

            std::cout << "[" << payload["timestamp"] << "] published: " << msg << std::endl;

            std::this_thread::sleep_for(std::chrono::milliseconds(PUBLISH_INTERVAL_MS));
        }

        // client.disconnect()->wait();
    } catch (const mqtt::exception& ex) {
        std::cerr << "MQTT error: " << ex.what() << std::endl;
        return 1;
    }
    return 0;
}
