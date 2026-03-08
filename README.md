# Acoustic Camera

**Note:** This Bachelor project is an unmaintained test implementation. For a great Python-based acoustic camera, please use **[Spectacoular](https://github.com/acoular/spectacoular)** instead, which is developed by the makers of Acoular.

This project aims to create an acoustic camera that can visualize sound sources in a room.

## Overview

Here is a brief overview of the project structure:

![alt text](overview.png "Title")

- UMA-16 v2 USB mic array

  https://www.minidsp.com/products/usb-audio-interface/uma-16-microphone-array

  <img width="440" height="484" alt="image" src="https://github.com/user-attachments/assets/84f5deac-0d34-4457-8b74-2cb7cc9ac711" />

- Fish-eye Camera + UMA-16 v2 USB mic array

  <img width="347" height="462" alt="image" src="https://github.com/user-attachments/assets/b0b04be2-1553-45b8-836c-9c582719711a" />

## Test

- Realtime test

  https://github.com/user-attachments/assets/d4487e37-53c0-410e-9096-0be138bd0e5e

- UI

  <img width="1191" height="759" alt="image" src="https://github.com/user-attachments/assets/47f6ec09-5e3c-4f83-bb23-eebc0655869e" />

- FOV settings

  <img width="1148" height="752" alt="image" src="https://github.com/user-attachments/assets/b3185c86-3eac-4459-8c22-a0d4c83427ac" />

## Requirements

### Hardware

- Microphone Array
- USB Camera (optional)

### Python packages

- Python == 3.11
- Acoular
- TensorFlow (optional)
- OpenCV (optional)
- Flask (optional)

## Environment

- Create a new environment:
  ```bash
  uv sync
  source .venv/bin/activate
  ```
## Usage
- To run with default settings.
  ```bash
  cd acoustic-camera
  python start.py
  ```
