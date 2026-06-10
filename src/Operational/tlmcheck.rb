require 'csv'
require 'cosmos'

# Fetches telemetry data for a given target, packet, and item
def fetch_telemetry(target, packet, item)
  tlm(target, packet, item)
end

# Collect data for a specified duration (in seconds)
def collect_data(duration)
  start_time = Time.now
  expected_end_time = start_time + duration
  data = []
  iteration = 0

  while Time.now < expected_end_time
    iteration += 1
    current_time = Time.now
    data_point = [
      current_time.strftime("%Y-%m-%d %H:%M:%S"),
      fetch_telemetry('ESAT_COM07', 'EPS_PACKET', 'EPS_BATTERY_CURRENT'),
      fetch_telemetry('ESAT10_WIFI', 'EPS_PACKET', 'EPS_BATTERY_CURRENT'),
      fetch_telemetry('ESAT11_WIFI', 'EPS_PACKET', 'EPS_BATTERY_CURRENT')]
    data << data_point

    # Calculate the next expected timestamp
    next_time = start_time + iteration
    sleep_duration = [next_time - Time.now, 0].max
    sleep(sleep_duration)
  end

  data
end

# Write data to a CSV file
def write_to_csv(data, filename)
  CSV.open(filename, 'w') do |csv|
    csv << ['Timestamp', 'COM07 Battery Current', 'ESAT10 Battery Current', 'ESAT11 Battery Current']
    data.each do |row|
      csv << row
    end
  end
end

# Define the duration for data collection in seconds
duration = 1000 # Example: 15 seconds

# Collect the data
telemetry_data = collect_data(duration)

# Define your output CSV file name
csv_filename = 'telemetry_data.csv'

# Write the collected data to the CSV
write_to_csv(telemetry_data, csv_filename)

puts "Data collection complete. Telemetry data written to #{csv_filename}"
