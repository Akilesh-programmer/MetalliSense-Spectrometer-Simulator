from opcua import Server, ua
from datetime import datetime
from simulate import simulate_reading


from opcua import ua
from datetime import datetime
from simulate import simulate_reading  # your simulation logic

def generate_reading_callback(parent, metal_grade, incorrect_elements_count):
    try:
        # Extract values in case they are Variants
        grade = metal_grade.Value if isinstance(metal_grade, ua.Variant) else metal_grade
        count = incorrect_elements_count.Value if isinstance(incorrect_elements_count, ua.Variant) else incorrect_elements_count

        result = simulate_reading(grade, count)
        reading_str = str(result)

        print(f"[{datetime.now()}] ✅ Generated Reading for {grade}")
        return [ua.Variant(reading_str, ua.VariantType.String)]

    except Exception as e:
        print("❌ Error in callback:", e)
        return [ua.Variant(f"Error: {str(e)}", ua.VariantType.String)]



class SpectrometerOPCUAServer:
    def __init__(self):
        self.server = Server()
        self.server.set_endpoint("opc.tcp://0.0.0.0:4840/spectrometer/")
        self.server.set_server_name("SimulatedSpectrometerServer")

        uri = "http://example.com/spectrometer"
        self.idx = self.server.register_namespace(uri)

        self.objects = self.server.get_objects_node()
        self.device = self.objects.add_object(self.idx, "Spectrometer")

        # Add config variables as writable
        self.metal_grade_node = self.device.add_variable(
            self.idx, "MetalGrade", "SG-Iron", ua.VariantType.String
        )
        self.metal_grade_node.set_writable()
        self.incorrect_elements_node = self.device.add_variable(
            self.idx, "IncorrectElementsCount", 2, ua.VariantType.Int32
        )
        self.incorrect_elements_node.set_writable()

        # Add temperature as a read-only variable
        self.temperature_node = self.device.add_variable(
            self.idx, "Temperature", 0.0, ua.VariantType.Double
        )
        # Not writable by client

        self.latest_reading_node = self.device.add_variable(
            self.idx, "LatestReading", "", ua.VariantType.String
        )
        self.latest_reading_node.set_writable()

        self.device.add_method(
            self.idx,
            "GenerateReading",
            self.generate_reading_callback,
            [],
            [ua.VariantType.String],
        )

    def generate_reading_callback(self, parent, *args):
        # Read config from variables
        grade = self.metal_grade_node.get_value()
        count = self.incorrect_elements_node.get_value()
        result = simulate_reading(grade, count)
        reading_str = str(result)
        self.latest_reading_node.set_value(reading_str)
        # Set temperature
        temp = result.get("temperature", 0.0)
        self.temperature_node.set_value(temp)
        print(f"[{datetime.now()}] ✅ Generated Reading for {grade}")
        return [ua.Variant(reading_str, ua.VariantType.String)]

    def generate_reading(self):
        grade = self.metal_grade_node.get_value()
        count = self.incorrect_elements_node.get_value()
        result = simulate_reading(grade, count)
        reading_str = str(result)
        self.latest_reading_node.set_value(reading_str)
        temp = result.get("temperature", 0.0)
        self.temperature_node.set_value(temp)
        print(f"[{datetime.now()}] ✅ Generated Reading for {grade}")
        return reading_str

    def run(self):
        self.server.start()
        print("✅ OPC-UA Server started at: opc.tcp://0.0.0.0:4840/spectrometer/")
        try:
            while True:
                pass
        finally:
            self.server.stop()
