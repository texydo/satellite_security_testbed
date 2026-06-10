require 'socket'
require 'cosmos'
require 'cosmos/script'
require 'time'
require 'inifile'
require 'pp'

# read an existing file || The absolute path for the file make sure the path is where the cosmos path in the ruby file
file = IniFile.load('RubySat\\rubysat\\sim_config.ini')
data = file["COSMOS_COM"]

server = TCPServer.new(data['cosmos_command_sender_IP'], Integer(data['cosmos_com_sender_PORT']))
puts "Server is running on 127.0.0.1:2345"

loop do
  begin
    client = server.accept
    message = client.gets
    if message
      message = message.strip
      if message != "exit"
        cmd(message)
        client.puts "Command executed"
      else
        client.puts "Exiting..."
        client.close
        break
      end
    else
      puts "Received an empty message"
    end
  rescue => e
    puts "Error during client connection: #{e.message}"
  ensure
    client.close if client
  end
end

puts "Server stopped..."
