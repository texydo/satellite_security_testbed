import datetime

from geomag import geomag
from skyfield.api import EarthSatellite, load
from skyfield.positionlib import ICRF, Barycentric, Geocentric
from skyfield.timelib import Time
from skyfield.toposlib import wgs84


class ProcessData:
    def __init__(self, tle) -> None:
        """
        Initializes the satellite object using TLE data and loads the ephemeris file.

        Args:
            tle (list): A list containing three strings:
                        - The satellite name
                        - Line 1 of the TLE
                        - Line 2 of the TLE

        Attributes:
            satellite (EarthSatellite): An EarthSatellite object initialized from the TLE.
            eph: The loaded ephemeris data from the 'de421.bsp' file.
        """
        self.satellite = self.get_satellite_from_tle(tle)
        self.eph = load("de421.bsp")

    @staticmethod
    def get_satellite_from_tle(tle: list) -> EarthSatellite:
        """
        Parses TLE (Two-Line Element) data and returns an EarthSatellite object.

        Args:
            tle (list): A list of three strings representing the satellite name and two TLE lines.

        Returns:
            EarthSatellite: An EarthSatellite object constructed from the given TLE data.
        """
        satellite_name = tle[0].strip()
        line1 = tle[1].strip()
        line2 = tle[2].strip()

        loaded_satellite = EarthSatellite(line1, line2, satellite_name)
        print(f"Loaded {loaded_satellite}")

        return loaded_satellite

    def get_satellite_snapshot(self, cur_timestamp_epoch: int) -> dict:
        """ "
        Generate a dictionary containing satellite data at a given timestamp.

        Parameters:
            cur_timestamp (skyfield.timelib.Time): The timestamp at which to retrieve the satellite's data.

        Returns:
            dict: A dictionary containing the following keys:
                - "Time": Formatted string representation of the timestamp.
                - "Longitude": Satellite subpoint longitude in degrees.
                - "Latitude": Satellite subpoint latitude in degrees.
                - "Altitude": Satellite altitude above Earth's surface in kilometers.
                - "Solar Intensity": Computed solar intensity at the satellite's position.
                - "Magnetic Field X": X component of the magnetic field at the satellite's subpoint.
                - "Magnetic Field Y": Y component of the magnetic field at the satellite's subpoint.
                - "Magnetic Field Z": Z component of the magnetic field at the satellite's subpoint.
        """
        timeInTimeScale = self.get_TS_FromEpochTime(cur_timestamp_epoch)
        pos = self.satellite.at(timeInTimeScale)
        lat, lon = pos.subpoint().latitude.degrees, pos.subpoint().longitude.degrees
        alt = wgs84.height_of(pos).km
        bx, by, bz = self.get_magnetic_field(lat, lon, alt)

        intensity = self.solar_intensity(pos, timeInTimeScale)

        new_row = {
            "Time": cur_timestamp_epoch,
            "Longitude": lon,
            "Latitude": lat,
            "Altitude": alt,
            "Solar Intensity": intensity,
            "Magnetic Field X": bx,
            "Magnetic Field Y": by,
            "Magnetic Field Z": bz,
        }

        return new_row

    def solar_intensity(
        self, pos: Geocentric | Barycentric | ICRF, cur_time: float
    ) -> float:
        """
        Calculates the solar intensity at a given satellite position and time.

        If the satellite is in sunlight, computes the distance to the Sun and uses
        the inverse square law to determine the solar power per square meter at that distance.

        Args:
            pos (Geocentric | Barycentric | ICRF): The satellite's position in a space-based frame.
            cur_time (float): The current simulation time in Julian days.

        Returns:
            float: The solar intensity in watts per square meter at the satellite's position.
                Returns 0 if the satellite is not sunlit.
        """
        if pos.is_sunlit(self.eph):
            # Get the geocentric position of the satellite
            geocentric_position = pos
            # Earth's position relative to the solar system barycenter
            earth_position = self.eph["earth"].at(cur_time)

            # Convert the satellite's position to a barycentric frame
            # Note: The satellite's position is returned in AU by Skyfield, so it's compatible
            satellite_barycentric_position = Barycentric(
                position_au=earth_position.position.au
                + geocentric_position.position.au,
                velocity_au_per_d=earth_position.velocity.au_per_d
                + geocentric_position.velocity.au_per_d,
                t=cur_time,
                center=0,  # Center at the Solar System Barycenter
            )

            # Add the ephemeris to the manually created Barycentric object
            satellite_barycentric_position._ephemeris = self.eph

            # Now, observe the Sun from the satellite's barycentric position
            sun = self.eph["sun"]
            observation = satellite_barycentric_position.observe(sun)

            # Calculate the distance to the Sun
            distance_to_sun_m = observation.distance().au

            # Solar constant
            solar_constant = 1361  # W/m^2 at 1 AU

            # Adjust intensity using the inverse square law
            intensity_at_distance = solar_constant / (distance_to_sun_m**2)

            return intensity_at_distance
        else:
            return 0

    @staticmethod
    def get_magnetic_field(latitude, longitude, altitude) -> tuple[float, float, float]:
        """
        Retrieves the Earth's magnetic field components at a given geographic location.

        Args:
            latitude (float): Latitude in degrees.
            longitude (float): Longitude in degrees.
            altitude (float): Altitude in kilometers.

        Returns:
            tuple[float, float, float]: The magnetic field vector components (bx, by, bz) in nanotesla (nT).
        """
        mag = geomag.GeoMag()
        magnetic_field = mag.GeoMag(latitude, longitude, altitude)
        return magnetic_field.bx, magnetic_field.by, magnetic_field.bz

    @staticmethod
    def get_TS_FromEpochTime(timeInEpochFormat: int) -> Time:
        """
        Converts an epoch timestamp to a Skyfield Time object.

        Args:
            timeInEpochFormat (int): The time in Unix epoch format (seconds since 1970).

        Returns:
            Time: A Skyfield Time object corresponding to the given timestamp.
        """
        dt = datetime.datetime.fromtimestamp(timeInEpochFormat, tz=datetime.timezone.utc)
        ts = load.timescale()
        t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
        return t

    def get_intensity(self, cur_timestamp):
        ts = self.get_TS_FromEpochTime(cur_timestamp)
        pos = self.satellite.at(ts)
        intensity = self.solar_intensity(pos, ts)
        return intensity
