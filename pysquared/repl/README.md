# Repl tests

These are tests designed to run in the repl on the flight control board.

For all of these tests you must copy the `repl/` directory from the root of the repo to the board.

## Radio Test
To run the radio test use the following:
```
from repl.radio_test import RadioTest
rt = RadioTest(config, c, "l")
rt.run()
```

Then come add more to this readme!
