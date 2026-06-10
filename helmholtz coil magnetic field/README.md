# Helmholtz Coil Magnetic Field

This repository folder contains the 3D design files for a Helmholtz coil magnetic field setup. It includes the main `HHC.pdf` 3D model/reference file, editable SolidWorks source parts, and exported STL files for 3D printing the fixture components.

A Helmholtz coil setup normally uses two matching circular coils placed on the same axis. When the coil spacing is close to the coil radius, the magnetic field near the center becomes relatively uniform. The parts in this folder look like support hardware for positioning coils, borders, a center hook, a tube/sample holder, and an LED holder around that coil geometry.

## File Types

| File type | Meaning | How to use it |
| --- | --- | --- |
| `.STL` | Exported 3D-print mesh files | Send these to a slicer for fabrication, or inspect them in a 3D viewer. |
| `.SLDPRT` | SolidWorks part files | Edit these in SolidWorks if dimensions or geometry need to change. |
| `.pdf` | Main 3D model/reference export | Open visually to understand the full Helmholtz coil design. |

## Printable STL Parts

Approximate sizes below were read from the STL mesh bounding boxes. They are useful for identifying the parts and estimating print volume. Check the CAD/model files before fabrication when exact dimensions are required.

| File | Approx. bounding size | Purpose |
| --- | ---: | --- |
| `45 angel coil holder.STL` | 10.0 x 70.2 x 26.0 mm | Coil holder for a 45 degree mounting position. |
| `45 angel coil holder_side1_coil760.STL` | 8.0 x 73.8 x 26.0 mm | Side 1 variant of the 45 degree coil holder for the 760 mm coil/frame configuration. |
| `45 angel coil holder_side2.STL` | 10.0 x 70.2 x 26.0 mm | Side 2 variant of the 45 degree coil holder. |
| `45 angel coil holder_side2_coil760.STL` | 8.0 x 73.8 x 26.0 mm | Side 2 variant for the 760 mm coil/frame configuration. |
| `90 angel coil holder.STL` | 34.0 x 10.0 x 51.0 mm | Coil holder for a 90 degree mounting position. |
| `HHC Led holder.STL` | 35.6 x 6.0 x 84.0 mm | Holder for mounting an LED on the Helmholtz coil setup. |
| `tube holder ver1.STL` | 58.2 x 44.5 x 58.2 mm | First version of a tube/sample holder. |
| `tube holder ver2.STL` | 28.0 x 29.0 x 28.0 mm | Second, smaller version of the tube/sample holder. |

Note: the filenames use `angel`; in this design context, this refers to the coil holder angle.

## SolidWorks Source Parts

These files are editable CAD source parts. Use them if you need to change dimensions, hole placement, thickness, fit, or export updated STL files.

| File | Role |
| --- | --- |
| `border 840.SLDPRT` | Border/frame part for an 840 mm configuration. |
| `border 870.SLDPRT` | Border/frame part for an 870 mm configuration. |
| `border 900.SLDPRT` | Border/frame part for a 900 mm configuration. |
| `center hook 830 20mm.SLDPRT` | Center hook part for an 830 mm configuration with a 20 mm feature. |
| `center hook 890 20mm.SLDPRT` | Center hook part for an 890 mm configuration with a 20 mm feature. |

The numbers in the filenames identify different frame/coil size variants.

## Main Model

`HHC.pdf` is the main 3D model/reference export for the Helmholtz coil fixture. It should be opened visually in a PDF viewer because the file does not contain extractable text.

Use the PDF to understand the intended assembly layout, then use the `.SLDPRT` files for CAD edits and the `.STL` files for printing.

## ESAT Hardware

| Subsystem | Description |
| --- | --- |
| Electrical Power Subsystem (EPS) | Two fixed solar panels, 5.5V at 180mA each; Li-ion battery pack, 6.0-8.4V; regulated outputs, 3.3V and 5V; battery protection for overvoltage, undervoltage, and overcurrent. |
| On-Board Computer (OBC) | MSP430F5529 MCU with 64KB flash; interfaces: I2C, SPI, UART; integrated Wi-Fi module; real-time clock (RTC). |
| Communication Subsystem (COM) | Operates at 425-525 MHz, default 433 MHz; supports 142-175 MHz and 850+ MHz interference-prone bands; modulation: OOK, 2FSK, 2GFSK, 4FSK, 4GFSK, CW; 32 channels with 250 kHz spacing; adjustable TX power from 0-100%. |
| Attitude Determination and Control Subsystem (ADCS) | 3-axis gyroscope, magnetometer, and IMU; orientation through magnetorquers and PID-controlled reaction wheel, 0-7000 RPM on the Z-axis. |
| Thermal Payload (TPL) | PWM-controlled heating element; powered by regulated 5V line. |
| Ground Station (GS) | Full-duplex RF communication using the same transceiver as the satellite; supports telemetry reception, command transmission, and logging. |

## Suggested Workflow

1. Open `HHC.pdf` to see the overall design.
2. Open the `.SLDPRT` files in SolidWorks if any dimensions need verification or modification.
3. Export revised STL files from SolidWorks if changes are made.
4. Slice the existing or revised `.STL` files for 3D printing.
5. Assemble the printed holders around the coil frame and verify coil alignment, center positioning, and tube/sample clearance.

## 9000 Lumen 100W LED Guide

The `HHC Led holder.STL` part is used to mount the LED in the Helmholtz coil setup. A 100W LED around 9000 lumen produces a lot of light and heat, so the LED must be mounted with proper cooling and electrical protection.

Basic build requirements:

- 100W LED module, about 9000 lumen.
- Constant-current LED driver matched to the LED voltage and current.
- Large aluminum heat sink.
- Thermal paste or thermal pad between the LED and heat sink.
- Fan cooling if the heat sink alone is not enough.
- Proper wires, insulation, and strain relief.
- `HHC Led holder.STL` for positioning the LED on the fixture.

Assembly notes:

1. Attach the LED module to the heat sink with thermal paste.
2. Mount the heat sink and LED into the printed LED holder.
3. Connect the LED only through a suitable constant-current driver.
4. Test the LED for a short time first and check the heat sink temperature.
5. Add fan cooling if the LED or heat sink becomes too hot.
6. Keep the LED beam away from eyes during testing.

Example video guide:

- [How to make a 100W LED light](https://www.youtube.com/watch?v=RaBrSJG9Dps)

## Important Checks Before Printing

- Confirm whether the coordinate units are millimeters in your slicer.
- Check that the coil size variants match the physical coil/frame being built.
- Verify which 45 degree holder variants are needed for side 1 and side 2.
- Check fit around the tube/sample holder before final printing.
- Use the SolidWorks files as the source of truth if the STL and PDF disagree.
- A 100W LED must not be powered directly from a normal power supply without a matching LED driver.
- A 9000 lumen LED is very bright; do not look directly into the LED while it is powered.
