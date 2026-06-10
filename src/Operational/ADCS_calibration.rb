prompt("ADCS calibration")
targets = get_target_list()
target = combo_box("Target ESAT", *targets)
loop do
  prompt("Place the ESAT on a steady surface to calibrate the gyroscope")
  cmd(target, "ADCS_DIAGNOSTICS_CONFIGURE_GYROSCOPE_BIAS_CORRECTION")
  last_packet_count = get_tlm_cnt(target, "ADCS_PACKET")
  wait("#{target} ADCS_PACKET RECEIVED_COUNT != #{last_packet_count}", 5)
  rotational_speed = tlm(target, "ADCS_PACKET", "ADCS_ROTATIONAL_SPEED")
  action = message_box("Measured rotational speed: #{rotational_speed} degrees per second\n(it should be 0 degrees per second)",
                       "Continue",
                       "Repeat")
  break if action == "Continue"
end
prompt("Place the ESAT back on the rotating table between the magnets")
cmd(target,
    "ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION",
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_0" => 0,
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_45" => 45,
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_90" => 90,
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_135" => 135,
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_180" => 180,
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_225" => 225,
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_270" => 270,
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_315" => 315)
positions = {0 => "+X panel (0 deg)",
             45 => "+X,+Y corner (45 deg)",
             90 => "+Y panel (90 deg)",
             135 => "-X,+Y corner (135 deg)",
             180 => "-X panel (180 deg)",
             225 => "-X,-Y corner (225 deg)",
             270 => "-Y panel (270 deg)",
             315 => "+X,-Y corner (315 deg)"}
measurements = {}
loop do
  positions.each_pair do |angle,feature|
    loop do
      prompt("Point the #{feature} towards the North magnet as accurately as possible")
      measurements[angle] = tlm(target, "ADCS_PACKET", "ADCS_MAGNETIC_ANGLE")
      action = message_box("Measured: #{measurements[angle]} degrees\n(expect it to be not too far from #{angle} degrees)",
                           "Continue",
                           "Repeat")
      break if action == "Continue"
    end
  end
  action2 = message_box("Measurementes:\n#{measurements[0]} deg at 0 deg.\n#{measurements[45]} deg at 45 deg.\n#{measurements[90]} deg at 90 deg.\n#{measurements[135]} deg at 135 deg.\n#{measurements[180]} deg at 180 deg.\n#{measurements[225]} deg at 225 deg.\n#{measurements[270]} deg at 270 deg.\n#{measurements[315]} deg at 315 deg.", 
                        "Repeat",
                        "Send")
  break if action2 == "Send"
end
cmd(target,
    "ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION",
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_0" => measurements[0],
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_45" => measurements[45],
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_90" => measurements[90],
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_135" => measurements[135],
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_180" => measurements[180],
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_225" => measurements[225],
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_270" => measurements[270],
    "PARAMETER_ADCS_DIAGNOSTICS_CONFIGURE_MAGNETOMETER_GEOMETRY_CORRECTION_MEASUREMENT_315" => measurements[315])
