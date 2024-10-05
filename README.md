# Launchpad Controller for Ableton Live

This project provides a custom controller script for using a Launchpad with Ableton Live. It enhances the functionality of the Launchpad by adding various modes and features for more intuitive music production and live performance.

## Features

- **Multiple Modes**: 
  - Session Mode
  - User 1 Mode (Mixer Mode)
  - User 2 Mode
  - Mixer Mode

- **Enhanced Session View**: 
  - Clip launching and scene triggering
  - Session overview with zooming functionality
  - Stop clip buttons

- **Mixer Controls**: 
  - Volume, pan, and send controls
  - Track selection

- **Custom Functionality**:
  - Delete clip button
  - Row duplication with long press

- **Configurable**: Easy to modify and extend for custom workflows

## Files

- `MainSelectorComponent.py`: Main component that manages different modes and button assignments
- `Log.py`: Logging utility for debugging and tracking script behavior
- `Settings.py`: Configuration settings for the script

## Setup

1. Place these files in your Ableton Live MIDI Remote Scripts folder
2. In Ableton Live, go to Preferences > Link MIDI
3. In the Control Surface dropdown, select "Launchpad"
4. Ensure your Launchpad is selected for input and output

## Usage

- Use the top row buttons to switch between modes
- In Session Mode:
  - Launch clips and scenes
  - Use the rightmost column for scene management (launch/delete)
  - Long press a scene button to duplicate the row
- In Mixer Mode:
  - Control various mixer parameters
  - Use sub-modes for different mixer functions

## Customization

You can modify the `MainSelectorComponent.py` file to change button behaviors or add new functionality. The `Settings.py` file allows you to enable/disable logging for debugging purposes.

## Dependencies

- Ableton Live 10 or later
- Compatible Launchpad device

## Contributing

Feel free to fork this project and submit pull requests for any enhancements or bug fixes.

## License

[Insert your chosen license here]