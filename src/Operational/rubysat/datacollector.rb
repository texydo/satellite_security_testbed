require 'socket'
require 'cosmos'
require 'cosmos/script'
require 'time'
require 'json'
require 'inifile'
require 'pp'

# read an existing file || The absolute path for the file  make sure the path is where the cosmos path in the ruby file
file = IniFile.load('RubySat\\rubysat\\sim_config.ini')
data = file["COSMOS_COM"]

def send_with_length(client, data)
  json_data = JSON.generate(data)
  length = json_data.bytesize
  packed_length = [length].pack("N")
  client.write(packed_length + json_data)
end

def fetch_packets
  {
    "TPL_PACKET" => get_tlm_packet("ESAT10_WIFI", "TPL_PACKET"),
    "PI_PAYLOAD_STATUS_PACKET" => get_tlm_packet("ESAT10_WIFI", "PI_PAYLOAD_STATUS_PACKET"),
    "EPS_PACKET" => get_tlm_packet("ESAT10_WIFI", "EPS_PACKET"),
    "OBC_PACKET" => get_tlm_packet("ESAT10_WIFI", "OBC_PACKET"),
    "OBC_PROCESSOR_PACKET" => get_tlm_packet("ESAT10_WIFI", "OBC_PROCESSOR_PACKET")
  }
end

server = TCPServer.new(data['cosmos_com_IP'], Integer(data['cosmos_com_PORT']))
puts "Server is running on localhost:34567"

Signal.trap("INT") do
  puts "Shutting down server..."
  server.close
  exit
end

loop do
  begin
    client = server.accept
    puts "Client connected"

    loop do
      packets = fetch_packets
      if packets.empty?
        puts "No packets available to send."
      else
        send_with_length(client, packets)
      end
      sleep(1)
    end

  rescue StandardError => e
    puts "Error during client connection: #{e.message}"
  ensure
    if client
      client.close
      puts "Client disconnected"
    end
  end
end

puts "Server stopped..."
