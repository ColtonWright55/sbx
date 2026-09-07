import CoreLocation
import Foundation
import UIKit

final class LocationManager: NSObject, CLLocationManagerDelegate {
    static let shared = LocationManager()

    private let manager = CLLocationManager()
    private var lastSentAt: Date?
    private let minInterval: TimeInterval = 5 * 60

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
        manager.allowsBackgroundLocationUpdates = true
        manager.pausesLocationUpdatesAutomatically = false
        manager.showsBackgroundLocationIndicator = true
        UIDevice.current.isBatteryMonitoringEnabled = true
    }

    func start() {
        manager.requestAlwaysAuthorization()
        manager.startUpdatingLocation()
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        let now = Date()
        if let last = lastSentAt, now.timeIntervalSince(last) < minInterval {
            return
        }
        lastSentAt = now
        send(location)
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {}

    private func send(_ location: CLLocation) {
        var task: UIBackgroundTaskIdentifier = .invalid
        task = UIApplication.shared.beginBackgroundTask {
            UIApplication.shared.endBackgroundTask(task)
        }

        var request = URLRequest(url: Config.serverURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "_type": "location",
            "tid": Config.trackerID,
            "lat": location.coordinate.latitude,
            "lon": location.coordinate.longitude,
            "acc": location.horizontalAccuracy,
            "alt": location.altitude,
            "vel": max(location.speed, 0) * 3.6,
            "batt": Int(UIDevice.current.batteryLevel * 100),
            "tst": Int(location.timestamp.timeIntervalSince1970),
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: request) { _, _, _ in
            UIApplication.shared.endBackgroundTask(task)
        }.resume()
    }
}
