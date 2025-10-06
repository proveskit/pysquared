# PySquared

**PySquared** is a CircuitPython-based CubeSat flight software library with [flight](https://space.skyrocket.de/doc_sdat/pleiades-orpheus.htm) [heritage](https://docs.proveskit.space/en/latest/#trials-and-tribulations-in-cubesats). It provides robust, modular components for spacecraft control, telemetry, configuration, and hardware management.

## Features

- Modular architecture for easy extension and customization
- Type-checked protocols and sensor interfaces
- Robust error handling and JSON-structured logging
- Configuration management with validation
- [High test coverage](https://sonarcloud.io/component_measures?metric=coverage&id=proveskit_circuitpy_flight_software)
- Designed for microcontroller resource constraints

## Quick Start

### Using PySquared for your Satellite

If you are looking to use PySquared in your own project, see the [Getting Started](https://proveskit.github.io/pysquared/getting-started/) guide.

### Contributing to PySquared

If you want to contribute to PySquared, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/proveskit/pysquared.git
   cd pysquared

   ```

1. Install dependencies using `uv`:

   ```bash
   make

   ```

1. Run tests:

   ```bash
   make test

   ```

1. See the [contributing](https://proveskit.github.io/pysquared/contributing/) guide for more details.

## Documentation

- [Getting Started](https://proveskit.github.io/pysquared/getting-started/)
- [Design Guide](https://proveskit.github.io/pysquared/design-guide/)
- [Configuration](https://proveskit.github.io/pysquared/api/#pysquared.config)
- [Error Handling & Logging](https://proveskit.github.io/pysquared/api/#pysquared.logger)
- [API Reference](https://proveskit.github.io/pysquared/api/)
- [Contributing](https://proveskit.github.io/pysquared/contributing/)

## Supported Platforms

- [PROVES Kit hardware](https://docs.proveskit.space/en/latest/)
- Devices [supported by CircuitPython](https://circuitpython.org/downloads)

## Contributing

We welcome contributions! Please read our [contributing guide](https://proveskit.github.io/pysquared/contributing/) and [design guide](https://proveskit.github.io/pysquared/design-guide/) before submitting changes. If you have questions, open an issue or discussion.
