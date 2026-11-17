import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
import cv2
from cv_bridge import CvBridge
import json
import paho.mqtt.client as mqtt

class SentinelCoreNode(Node):
    def __init__(self):
        super().__init__('sentinel_core_node')
        
        # ROS 2 Subscriptions & Publishers
        self.bridge = CvBridge()
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)
        self.alert_pub = self.create_publisher(
            String, '/sentinel/alerts', 10)

        # MQTT Telemetry Setup
        self.mqtt_client = mqtt.Client(client_id="ROS2_Sentinel_Bridge")
        try:
            self.mqtt_client.connect("localhost", 1883, 60)
            self.mqtt_client.loop_start()
            self.get_logger().info("Connected to MQTT Broker.")
        except Exception as e:
            self.get_logger().warn(f"MQTT connection failed: {e}")

        self.latest_scan_dist = 0.0

    def scan_callback(self, msg):
        # Extract minimum distance to nearest obstacle
        if len(msg.ranges) > 0:
            valid_ranges = [r for r in msg.ranges if r > msg.range_min and r < msg.range_max]
            if valid_ranges:
                self.latest_scan_dist = min(valid_ranges)

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # --- AI / ML Processing Placeholder ---
            # Perform object detection, anomaly detection, or terrain analysis here
            detection_detected = False
            
            # Simple threshold check for demonstration
            if self.latest_scan_dist < 1.0 and self.latest_scan_dist > 0.0:
                detection_detected = True

            payload = {
                "system_status": "OPERATIONAL",
                "min_obstacle_dist": round(float(self.latest_scan_dist), 2),
                "alert_triggered": detection_detected
            }

            # Publish to ROS 2 topic
            alert_msg = String()
            alert_msg.data = json.dumps(payload)
            self.alert_pub.publish(alert_msg)

            # Bridge data to MQTT Web Dashboard
            self.mqtt_client.publish("sentinel/telemetry", json.dumps(payload))

        except Exception as e:
            self.get_logger().error(f"Failed to process frame: {e}")

    def destroy_node(self):
        self.mqtt_client.loop_stop()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SentinelCoreNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()