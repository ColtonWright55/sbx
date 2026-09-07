import Foundation

enum Config {
    // Your box's Tailscale IP/hostname, port 8000, hitting the existing /owntracks endpoint.
    static let serverURL = URL(string: "http://100.99.208.97:8000/owntracks")!
    static let trackerID = "CW"
}
