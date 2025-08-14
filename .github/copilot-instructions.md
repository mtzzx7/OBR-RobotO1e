# Copilot Instructions for OBR-RobotO1e

## Project Overview
This repository contains the main control code for a LEGO robot designed for the OBR (Olimpíada Brasileira de Robótica) competition. The code is written in Python and targets the Pybricks platform, using the PrimeHub and various sensors/motors.

## Architecture & Key Files
- **main.py**: The entire robot logic is implemented here. It includes:
  - Hardware initialization (motors, sensors, hub)
  - PID-based line following and movement routines
  - Gyro-based turns and heading correction
  - Color/HSV-based surface and object detection
  - Rescue and obstacle handling routines
  - The main async entrypoint is `main()`; execution starts with `run_task(main())` (do not remove this line)
- **.robotName, .robotNameList**: Used for robot identification; do not remove or rename.

## Critical Workflows
- **Run**: Upload and run `main.py` on the robot. The program starts automatically due to `run_task(main())` at the end of the file.
- **Debug**: Use print statements for debugging; output is visible via the Pybricks app/console.
- **Edit**: All logic is in `main.py`. Refactor with care—async/await is used throughout for multitasking.

## Project-Specific Patterns & Conventions
- **Async/Await**: All robot actions and routines are async. Use `await wait(0)` for yielding control.
- **PID Control**: PID parameters are global and can be reset/adapted in routines. See `redefinir_pid`, `PID`, and `redefinir`.
- **Sensor/Color Handling**: Color and HSV checks are encapsulated in functions like `is_prata`, `is_verde`, etc.
- **Gyro/IMU**: Heading corrections use residual error logic. See `zerar_heading_residual` and `gyro_turn`.
- **Rescue Logic**: Rescue routines are modular (`resgate_dir`, `resgate_esq`, etc.) and use global state flags.
- **Do not remove**: The final `run_task(main())` is required for program startup.

## Integration & Dependencies
- **Pybricks**: All hardware APIs are from the Pybricks library. No external Python dependencies.
- **No build/test scripts**: All logic is in `main.py`; there are no automated tests or build steps.

## Examples
- To add a new movement, create an `async def` function and call it from `main()` or a rescue routine.
- To tune PID, adjust `pid_p`, `pid_i`, `pid_d` at the top of `main.py` or within `redefinir`.

## References
- See `main.py` for all logic and conventions.
- For robot names, see `.robotName` and `.robotNameList`.

---
If you are unsure about a workflow or convention, review `main.py` for examples. When in doubt, preserve async structure and global state usage.
