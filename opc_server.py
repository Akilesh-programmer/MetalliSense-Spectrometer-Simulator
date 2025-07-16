from opcua import Server, ua
from datetime import datetime
from simulate import simulate_reading


class SpectrometerOPCUAServer:
    def __init__(self):
        self.server = Server()
        self.server.set_endpoint("opc.tcp://0.0.0.0:4840/spectrometer/")
        self.server.set_server_name("SimulatedSpectrometerServer")

        uri = "http://example.com/spectrometer"
        self.idx = self.server.register_namespace(uri)

        self.objects = self.server.get_objects_node()
        self.device = self.objects.add_object(self.idx, "Spectrometer")

        self.device.add_method(
            self.idx,
            "GenerateReading",
            self.generate_reading,
            [ua.VariantType.String, ua.VariantType.Int32],  # Inputs: grade, incorrect_count
            [ua.VariantType.String],  # Output: JSON string of reading
        )

        self.latest_reading_node = self.device.add_variable(
            self.idx, "LatestReading", "", ua.VariantType.String
        )
        self.latest_reading_node.set_writable()

    def generate_reading(self, parent, metal_grade, incorrect_elements_count):
        try:
            grade = metal_grade.Value if isinstance(metal_grade, ua.Variant) else metal_grade
            count = incorrect_elements_count.Value if isinstance(incorrect_elements_count, ua.Variant) else incorrect_elements_count

            result = simulate_reading(grade, count)
            reading_str = str(result)
            self.latest_reading_node.set_value(reading_str)
            print(f"[{datetime.now()}] Generated Reading for {grade}")
            return [ua.Variant(reading_str, ua.VariantType.String)]
        except Exception as e:
            return [ua.Variant(f"Error: {str(e)}", ua.VariantType.String)]


    def run(self):
        self.server.start()
        print("OPC-UA Server started at: opc.tcp://0.0.0.0:4840/spectrometer/")
        try:
            while True:
                pass
        finally:
            self.server.stop()

