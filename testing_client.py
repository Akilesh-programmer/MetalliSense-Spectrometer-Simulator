from opcua import Client, ua
import time

client = Client("opc.tcp://localhost:4840/spectrometer/")

try:
    client.connect()
    print("✅ Connected to OPC UA Server")

    # Get the root node
    root = client.get_root_node()

    # Browse to the Spectrometer object
    spectrometer_obj = root.get_child([
        "0:Objects", 
        "2:Spectrometer"
    ])

    # Get config variable nodes
    metal_grade_node = spectrometer_obj.get_child("2:MetalGrade")
    incorrect_elements_node = spectrometer_obj.get_child("2:IncorrectElementsCount")
    latest_reading_node = spectrometer_obj.get_child("2:LatestReading")

    # Set config variables
    metal_grade_node.set_value(ua.Variant("SG-Iron", ua.VariantType.String))
    incorrect_elements_node.set_value(ua.Variant(3, ua.VariantType.Int32))
    print("✅ Config variables set. Waiting for operator to generate reading...")

    # Get the current value of LatestReading
    last_reading = latest_reading_node.get_value()

    # Poll for new reading
    while True:
        new_reading = latest_reading_node.get_value()
        if new_reading != last_reading and new_reading != "":
            print("✅ New reading received:", new_reading)
            break
        time.sleep(1)

except Exception as e:
    print("❌ Error:", e)
finally:
    client.disconnect()
