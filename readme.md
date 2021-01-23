# ToDo's:

## Logging

- when state changes and `L1::step()` prints it, the 'friendly' version should be used for logs

  Same as in Gen, all `L2::get_state()` should support `friendly_output` option

- reduce logs to bare minimum

  ideally specify the level of details in `config/agents.yaml`

## Usability

### Minor

- in case run counter is not present, replace it with 0-count

- remove commented `__init__()` and other unused L2 functions, which were moved to L1

### Major

- `.yaml` specify for each map
  - the (x,y) coords for barracks and depos 
  - cut-off to determine up/down of the map?




