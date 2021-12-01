# Generation 3: decision pipeline

## Current ToDo's

Qs:
- who decides what builder should build next? Bob has its own DQN... Should it decide itself?
- Gen has its own, completely independent DQN? Looks like it does NOT assign tickets to Bob? The only set of actions is attack/wait/retreat?
  - Gen also have pipilene (only current vision): 


Short Run ToDo's (2021-10-04):
- Leave only 1 (joint?) log for the learning
- Implement Learning via _logger_
- confirm that DQN matrix is growning

Main bug:
- No orders for the 2nd+ game (seems OK though)
- Learning is only for the 1st game according to DQN_aiWarPlanner.dbg
- though DQN file is being updaed


Long Run ToDo's:
- bring back the attack Reserve/TF
- Sgt attacks with TF
- idle SCVs -> back to work (done)

???
'All barracks are full at the moment' is often at the beginning

Works: Builds
- marines
- SDs
- BKs





## Current focus

Draft for `Pipeline::Run()`

Status dictionary:
- Suitable for Run() (? **all statuses to `Waiting`** ?)
  - `Init`: once the ticket is created
  - `Ready`: unclear at the moment
  - `In Review`: blocked was removed
  - `Waiting`: _soft_ block. E.g. waiting for minerals or gas
- Ignored by Run()
  - `Done`: Completed and should be ignored for future
  - `Blocked`: Cannot be done until another ticket (one or many) is Done


Scan through all tickets in the pipeline
- if this list is empty, then order from Gen is complete!

`[CP1]:` checkpoint

Init:
- `blockers_removed = False` 
- empty list of `processed_tickets=[]`

Scan through all tickets in the pipeline, which are not in `processed_tickets` list
- if this list is empty, then `return None`


*If* any of the tickets report, that it is `[ret]ticket_was_esolved:true` *then*:
- change ticket status to `Done`
- check *if* it was blocking any other tickets (*obsolete*)
  - *if* `True` *then* `blockers_removed = True` (*obsolete*)
- _if_ `[ret]sc2_order` is not `None` (meaning, that the order has produced something for the SC2 engine)
  - *then* `return [ret]sc2_order` (is is supposed to be one of the SC2 orders)
- add current ticket ID to `processed_tickets` list

Once the loop is complete check:  (*obsolete*)
*if* `blockers_removed == True` *then* rerun the loop above
*else* return None

rerun the loop above from `[CP1]:` checkpoint


### Key features:

- single AI to make a decision, when the previous order is accomplished
  if previous order was not complete, map the current with the same action (decision)
- Bob: pipeline agent just checks what is the current decision and fullfills it
- Tom: checks if there are any SCVs, which are doing nothing, bring the back to work
- Sgt peps: uses TF1 to do constant attacks

---

# Done

## Refactoring into multiple classes
 - separation of agent and econ_ function
 
## Logging

- when state changes and `L1::step()` prints it, the 'friendly' version should be used for logs

  Same as in Gen, all `L2::get_state()` should support `friendly_output` option

- reduce logs to bare minimum

  ideally specify the level of details in `config/agents.yaml`

## Usability

### Minor

- in case run counter is not present, replace it with 0-count

- remove commented `__init__()` and other unused L2 functions, which were moved to L1

# Later (long run) ToDo

### Major

- `.yaml` specify for each map
  - the (x,y) coords for barracks and depos 
  - cut-off to determine up/down of the map?




