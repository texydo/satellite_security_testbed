import struct
from skyfield.api import load
from skyfield.api import EarthSatellite
from skyfield.positionlib import Barycentric, Geocentric, ICRF
import msgpack
import yaml
from geomag import geomag
from skyfield.toposlib import wgs84


def receive_msgpack(comp_socket) -> dict:
    length_bytes = comp_socket.recv(4)
    if not length_bytes:
        return {}
    length = struct.unpack('I', length_bytes)[0]

    packed_data = b""
    while len(packed_data) < length:
        chunk = comp_socket.recv(1024)
        if not chunk:
            break
        packed_data += chunk

    if packed_data:
        msg = msgpack.unpackb(packed_data, raw=False)
        return msg
    return {}


def send_msgpack(comp_socket, msg):
    packed_data = msgpack.packb(msg, use_bin_type=True)
    length = struct.pack('I', len(packed_data))
    comp_socket.sendall(length + packed_data)


def serialize_yaml(path: str):
    with open(path, 'r') as yaml_file:
        data = yaml.safe_load(yaml_file)

    return data


# -------------------------------------------------------------------------------------------------------- Data Process

class ProcessData:
    def __init__(self, tle, _start_time: float) -> None:
        self.satellite = self.get_satellite_from_tle(tle)
        self.start_time = _start_time
        self.eph = load('de421.bsp')

    @staticmethod
    def get_satellite_from_tle(tle: list) -> EarthSatellite:
        satellite_name = tle[0].strip()
        line1 = tle[1].strip()
        line2 = tle[2].strip()

        loaded_satellite = EarthSatellite(line1, line2, satellite_name)
        print(f"Loaded {loaded_satellite}")

        return loaded_satellite

    def get_row(self, cur_timestamp) -> dict:
        pos = self.satellite.at(cur_timestamp)
        lat, lon = pos.subpoint().latitude.degrees, pos.subpoint().longitude.degrees
        alt = wgs84.height_of(pos).km
        bx, by, bz = self.get_magnetic_field(lat, lon, alt)

        intensity = self.solar_intensity(pos, cur_timestamp)

        new_row = {
            "Time": str(cur_timestamp)[9:-1],
            "Longitude": lon,
            "Latitude": lat,
            "Altitude": alt,
            "Solar Intensity": intensity,
            "Magnetic Field X": bx,
            "Magnetic Field Y": by,
            "Magnetic Field Z": bz
        }

        return new_row

    def solar_intensity(self, pos: Geocentric | Barycentric | ICRF, cur_time: float) -> float:
        if pos.is_sunlit(self.eph):
            # Get the geocentric position of the satellite
            geocentric_position = pos
            # Earth's position relative to the solar system barycenter
            earth_position = self.eph['earth'].at(cur_time)

            # Convert the satellite's position to a barycentric frame
            # Note: The satellite's position is returned in AU by Skyfield, so it's compatible
            satellite_barycentric_position = Barycentric(
                position_au=earth_position.position.au + geocentric_position.position.au,
                velocity_au_per_d=earth_position.velocity.au_per_d + geocentric_position.velocity.au_per_d,
                t=cur_time,
                center=0  # Center at the Solar System Barycenter
            )

            # Add the ephemeris to the manually created Barycentric object
            satellite_barycentric_position._ephemeris = self.eph

            # Now, observe the Sun from the satellite's barycentric position
            sun = self.eph['sun']
            observation = satellite_barycentric_position.observe(sun)

            # Calculate the distance to the Sun
            distance_to_sun_m = observation.distance().au

            # Solar constant
            solar_constant = 1361  # W/m^2 at 1 AU

            # Adjust intensity using the inverse square law
            intensity_at_distance = solar_constant / (distance_to_sun_m ** 2)

            return intensity_at_distance
        else:
            return 0

    @staticmethod
    def get_magnetic_field(latitude, longitude, altitude) -> tuple[float, float, float]:
        mag = geomag.GeoMag()
        magnetic_field = mag.GeoMag(latitude, longitude, altitude)
        return magnetic_field.bx, magnetic_field.by, magnetic_field.bz