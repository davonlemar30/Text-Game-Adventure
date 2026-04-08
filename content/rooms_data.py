"""Room content data for Zombie Apocalypse: The Mansion.

Data-only module intentionally separated from game logic.
"""

ROOMS_CONTENT = {'basement': {'name': 'Basement',
              'brief': 'Cold steel and chemical rot. You woke up here.',
              'description': 'You are in the Basement Lab.\n'
                             'The air is thick — stale chemicals, dried blood, something rotten.\n'
                             'A cold steel operating table sits in the centre, IV tubes dangling\n'
                             'loose. Nearby, an empty suspension tank looms — reinforced glass fogged,\n'
                             'dark residue clinging to the inside.\n'
                             "A heavy metal door to the east is labelled 'Lab Wing Access' — locked.\n"
                             'Stairs lead north toward the rest of the house.',
              'exits': {'north': 'entrance_hall'},
              'locked_exits': {'east': 'lab_wing'},
              'items': {'flashlight': 'A heavy-duty flashlight. Batteries still work.',
                        "mel's notebook": "A small blood-smeared notebook. Cover reads 'M. Peoples'.",
                        "elias's diary page": 'A torn diary page. Bloodstained robe nearby.',
                        'research log': 'A partially burned research log.'},
              'objects': {'operating table': 'Cold steel with restraint marks worn into the sides.\n'
                                             'The IV tubes were ripped out, not removed carefully.\n'
                                             'Someone left in a hurry. Or was taken.',
                          'suspension tank': 'An empty reinforced glass tank — large enough for a person.\n'
                                             'Dark residue inside. A discoloured ring on the floor beneath.\n'
                                             'Whatever was kept here was removed without being shut down.',
                          'blood trail': 'A smear of dried blood leads from the operating table\n'
                                         'toward the far wall and disappears into shadow.\n'
                                         "Whoever left this — it wasn't long ago.",
                          'lab door': "Heavy steel. 'Lab Wing Access.'\n"
                                      'A card reader on the wall beside it — dark. No power.\n'
                                      'The generator could change that.',
                          'medical cart': 'Overturned. Scattered syringes. One still has dark,\n'
                                          "viscous residue inside. You don't pick it up.",
                          'generator': 'A large diesel generator. Fuel gauge: a quarter tank.\n'
                                       'A pull cord along the right side, stiff from disuse.\n'
                                       'Enough fuel to run. It just needs to be started.\n'
                                       '(Try: USE FLASHLIGHT ON GENERATOR, or START GENERATOR)'}},
 'entrance_hall': {'name': 'Entrance Hall',
                   'brief': 'The front door is barricaded — nailed shut from this side. Not your way out.',
                   'description': 'You are in the Entrance Hall.\n'
                                  'A chandelier hangs above — crystals coated in dust and cobwebs.\n'
                                  'The front doors are barricaded with planks nailed haphazardly.\n'
                                  'Scratch marks at the base of the doors from the inside.\n'
                                  'A grand staircase to the right, its railing splintered.\n'
                                  'Passages lead west to the parlour, east to a cloakroom, north deeper in.',
                   'exits': {'south': 'basement', 'west': 'parlor', 'east': 'cloakroom', 'north': 'living_room'},
                   'locked_exits': {},
                   'items': {},
                   'objects': {'front door': 'Heavy wood, barricaded from the inside — thick planks nailed hard.\n'
                                             'Scratch marks at the base: deep, ragged. Fingernails.\n'
                                             "Something tried to get OUT, not in. They didn't make it.\n"
                                             '\n'
                                             "The door is sealed. You'd need a crowbar or something heavy\n"
                                             "to pry the planks loose — and that's if you even want to go out there.\n"
                                             'Through the gap: still, grey light. Shapes in the distance. Slow ones.\n'
                                             '\n'
                                             "This isn't your exit. Not yet.",
                               'scratch marks': 'Long ragged gouges at floor level. Multiple sets.\n'
                                                'They all faced the same direction — toward the door. Toward outside.\n'
                                                'None of them made it.',
                               'chandelier': 'Once grand. Several crystals missing. It sways faintly\n'
                                             "even though there's no wind you can feel.\n"
                                             'The chain looks old.',
                               'staircase': 'Wide stairs. One baluster missing, another cracked.\n'
                                            'Dried blood on the third step — a smear that trails up and stops.',
                               'bloodstain': 'A dark stain near the front door. The shape suggests someone\n'
                                             'sat here for a while. Bleeding. Waiting.\n'
                                             'Whatever they were waiting for never came.'}},
 'parlor': {'name': 'Parlor',
            'brief': 'Everything preserved under sheets. Like no one dared disturb it.',
            'description': 'You are in the Parlor.\n'
                           'Antique furniture under dusty white sheets — preserved, undisturbed.\n'
                           'A grand mirror above a cold fireplace, cracked diagonally.\n'
                           'A broken phonograph in the corner, needle stuck.\n'
                           'The air is stale — aged wood and something faintly floral.',
            'exits': {'east': 'entrance_hall'},
            'locked_exits': {},
            'items': {'guestbook': 'A dust-covered guestbook. Pages brittle.',
                      'energy bars': 'Three sealed protein bars stashed behind the phonograph. Still good.'},
            'objects': {'phonograph': 'The needle is stuck in a groove. Someone set it playing\n'
                                      'deliberately before they left. You wonder what the last song was.',
                        'mirror': 'Cracked diagonally. Your reflection is split — two versions\n'
                                  'of you, slightly offset. You look pale. Paler than you should.\n'
                                  'You look away before the other one does.',
                        'fireplace': 'Cold. Grey ash in the grate. Among the ash, a scrap of\n'
                                     "burned paper. One word still legible: 'Shelly.'",
                        'armchair': 'Dried blood on the right armrest. Someone sat here,\n'
                                    'injured, and stayed for a while. The indent in the cushion\n'
                                    'is still there — deep. They were here for days.\n'
                                    '\n'
                                    'Wait. Something is wedged between the cushion and the armrest.',
                        'tea set': "Tipped over. Cups shattered. Whoever left didn't look back.\n"
                                   'Tea stains on the tablecloth — long since dry.'}},
 'cloakroom': {'name': 'Cloakroom',
               'brief': 'Dust-heavy coats. A locked cabinet. One coat missing from the rack.',
               'description': 'You are in the Cloakroom.\n'
                              'A narrow space lined with coat racks and a storage cabinet.\n'
                              'Dust-covered coats hang lifelessly. The floor creaks underfoot.\n'
                              'A small mirror on the wall, cracked at one corner.',
               'exits': {'west': 'entrance_hall'},
               'locked_exits': {},
               'items': {'bottled water': 'A sealed bottle tucked deep in a coat pocket. Cold.'},
               'objects': {'mirror': 'Cracked at the corner. Your reflection is distorted —\n'
                                     'one eye lower than the other, jaw at the wrong angle.\n'
                                     "You know it's just the crack.",
                           'coats': 'Old coats, thick with dust. One rack has a gap —\n'
                                    'a coat is missing. The hanger still swings faintly.\n'
                                    'House keys in one of the remaining pockets. No use to you.',
                           'cabinet': 'A locked wooden cabinet. Basic padlock.\n'
                                      "You'd need something thin and rigid to open it.",
                           'hat': 'A hat on the floor, brim thick with dust.\n'
                                  "It's been there for weeks. The owner didn't come back."}},
 'living_room': {'name': 'Living Room',
                 'brief': 'Overturned furniture. A letter placed deliberately in the middle of the floor.',
                 'description': 'You are in the Living Room.\n'
                                'A shattered television on its side. An overturned bookcase scattering\n'
                                'papers and broken frames across the floor. A photograph on the\n'
                                'mantelpiece facing down.\n'
                                'A crumpled letter sits in the centre of the floor — placed, not dropped.',
                 'exits': {'east': 'entrance_hall', 'south': 'kitchen', 'north': 'master_bedroom'},
                 'locked_exits': {'west': 'quarantine_room'},
                 'items': {"kristy's letter": 'A bloodstained letter. Placed deliberately.'},
                 'objects': {'photograph': 'Face-down on the mantelpiece. You turn it over:\n'
                                           'a man — younger, smiling — with a woman and a small girl.\n'
                                           "On the back: 'We'll do this together.'\n"
                                           "The man is Dr. Barbados. You don't know how you know that.",
                             'quarantine door': 'A heavy reinforced door set into the west wall.\n'
                                                'Sliding bolt and keyhole — both engaged.\n'
                                                'The wood on the far side is scored with deep, even lines.\n'
                                                'Tally marks. You count them before you can stop yourself.\n'
                                                'Forty-three.',
                             'television': 'Screen caved in — something hit it hard.\n'
                                           'A bloodstain on the corner. Plug still in the wall.',
                             'bookcase': 'Toppled. Among the papers, a loose research journal page —\n'
                                         "equations you don't understand. At the bottom, underlined:\n"
                                         "'Do not proceed to Stage 3.'",
                             'mantelpiece': 'Cold stone. The photograph and undisturbed dust.\n'
                                            'One small handprint in the dust — too small for an adult.'}},
 'kitchen': {'name': 'Kitchen',
             'brief': "Stripped bare. Chemical smell. Don't make sparks.",
             'description': 'You are in the Kitchen.\n'
                            'The cabinets hang open and empty — stripped.\n'
                            'Floorboards near the pantry door have collapsed inward.\n'
                            'A faint chemical smell in the air. Not food. Something piped.\n'
                            'Be careful with anything that makes a spark.',
             'exits': {'north': 'living_room', 'east': 'study'},
             'locked_exits': {},
             'items': {'food supplies': 'A dented tin of canned goods and some sealed protein bars.',
                       'water bottle': 'A full sealed water bottle.'},
             'objects': {'cabinets': 'Every shelf emptied. Someone was here before you.\n'
                                     'One cabinet door is hanging off its hinge.',
                         'floorboards': 'Several boards near the pantry collapsed into a dark space below.\n'
                                        "The gap isn't large enough to fit through.\n"
                                        'The smell coming up is bad — rot and standing water.',
                         'stove': 'Old gas stove. One burner knob turned slightly — not all the way.\n'
                                  "That explains the smell. Don't use open flame in this room.",
                         'sink': 'Bone dry. Both taps open, nothing coming out.\n'
                                 'Dead plant on the windowsill. Through the window: empty garden.'}},
 'study': {'name': 'Study',
           'brief': "Research notes everywhere. One line pinned to the wall: 'Trust no one.'",
           'description': 'You are in the Study.\n'
                          'A desk covered in handwritten research notes. Bookshelves\n'
                          'lining the walls, one toppled. A dark computer terminal — no power.\n'
                          "Pinned to the wall, underlined twice: 'Trust no one.'",
           'exits': {'west': 'kitchen'},
           'locked_exits': {},
           'items': {'walkie-talkie': 'A military-grade walkie-talkie. Charged. Only static.',
                     'quarantine key': "A heavy key on a red lanyard. Labelled 'Q-ROOM'.",
                     'voice recorder': 'A cracked voice recorder. Indicator light still blinking.'},
           'objects': {'desk': 'Covered in research notes. Cell diagrams. Equations.\n'
                               "'Stage 2 replication' and 'neural bridge — viable?' throughout.\n"
                               'Last page is blank except four words pressed hard into the paper:\n'
                               "'What have I done.'",
                       'terminal': 'Dark. No power.\n'
                                   "Sticky note on screen: 'Camera log — 3 entries. Remote access required.'\n"
                                   'If the generator were running, you might access it.',
                       'bookshelves': 'Medical and biology texts. One shelf swept completely clear.\n'
                                      "In the gap, scratched into the wood: 'RUN'",
                       'research notes': 'Dozens of loose pages. Neural pathways. Toxicology.\n'
                                         'Then a shift — infection vectors. Reanimation timelines.\n'
                                         'The handwriting gets messier toward the end.\n'
                                         "The final few pages are written in something that isn't ink.",
                       'safe': 'A small wall safe behind a pulled-aside shelf.\n'
                               "Combination lock. You'd need the combination."}},
 'master_bedroom': {'name': 'Master Bedroom',
                    'brief': 'Torn sheets. A handprint smeared down the wall. Empty pill bottles.',
                    'description': 'You are in the Master Bedroom.\n'
                                   'A large bed with torn sheets, half-pulled to the floor.\n'
                                   'The closet door hangs ajar. A bloody handprint smeared down the\n'
                                   'wall beside the window — someone slid. Empty medication bottles\n'
                                   'on the nightstand. The room smells like something that ended badly.',
                    'exits': {'south': 'living_room', 'east': 'bathroom'},
                    'locked_exits': {},
                    'items': {'first aid kit': 'A proper medical kit — sealed. Bandages, antiseptic, sutures.',
                              "kristy's journal": 'A leather-bound journal. Dried blood on the cover.'},
                    'objects': {'bloody handprint': 'A single handprint on the wall, smeared downward.\n'
                                                    "The print is small. A woman's hand.",
                                'closet': 'Inside: clothes on hangers, shoes on the floor, a scarf\n'
                                          'torn cleanly in half. Nothing missing except who wore these.',
                                'nightstand': "Three empty pill bottles — prescribed to 'K. O'Hara.'\n"
                                              "Anxiety. Insomnia. And a third label you don't recognise.\n"
                                              'All empty. Finished, not spilled.',
                                'window': 'Cracked. Curtains drawn but light bleeds through.\n'
                                          'Through it: the overgrown garden, and shapes beyond.\n'
                                          'Slow. Aimless. More than you can count.\n'
                                          "They haven't noticed the house yet."}},
 'bathroom': {'name': 'Bathroom',
              'brief': 'A figure in a hospital gown, slumped against the bathtub. Not quite still.',
              'description': 'You are in the Bathroom.\n'
                             'A cracked mirror above a dry sink. Stained tiles.\n'
                             'A figure in a hospital gown is slumped against the bathtub.\n'
                             'The smell is very bad. Move carefully.',
              'exits': {'west': 'master_bedroom'},
              'locked_exits': {},
              'items': {},
              'objects': {'mirror': 'Cracked in several places. Your reflection fragments across\n'
                                    'the breaks — pale, hollow, fractured.\n'
                                    "One reflection doesn't quite line up with the others.\n"
                                    "You tell yourself it's the angle.",
                          'figure': 'A zombie. Former patient — hospital gown, bare feet, IV port still taped\n'
                                    'to its arm. It stirs when you get close. Not aggressive yet.\n'
                                    'But it will be if you make noise.\n'
                                    'It was a person once. Not long ago.\n'
                                    '(EXAMINE FIGURE to engage.)',
                          'sink': 'Bone dry. Tap rusted open, nothing coming out.\n'
                                  'A ring of grime where water used to reach.',
                          'medicine cabinet': 'Above the sink, door hanging open.\n'
                                              'Empty — mostly. One unused syringe still in packaging.\n'
                                              'You leave it.',
                          'bathtub': 'Dry. A dark ring marks the old waterline.\n'
                                     "The bottom is stained in a way that wasn't just water."}},
 'quarantine_room': {'name': 'Quarantine Room',
                     'brief': 'Tally marks cover every wall. Something breathes in the dark.',
                     'description': 'You are in the Quarantine Room.\n'
                                    'The walls are covered in long, deliberate scratch marks — measured,\n'
                                    'evenly spaced. Tally marks. The decay smell is overwhelming.\n'
                                    'The room is dark beyond what your flashlight reaches.\n'
                                    'You can hear breathing. Slow. Patient.',
                     'exits': {'east': 'living_room'},
                     'locked_exits': {},
                     'items': {},
                     'objects': {'scratch marks': 'Rows of parallel lines etched deep into the plaster.\n'
                                                  'You count them. You stop counting.\n'
                                                  "You don't want to know how long he's been in here.",
                                 'darkness': 'The corners are absolute black.\n'
                                             "You can't see what's there.\n"
                                             'But you can hear it breathing.',
                                 'barbados': "He's here. Still — until he isn't.\n"
                                             'His eyes catch your light: pale, luminous, aware.\n'
                                             'He turns toward you slowly. All the time in the world.\n'
                                             'Like someone who has been waiting specifically for you.\n'
                                             "He knows you're here. He knew before you opened the door."}},
 'lab_wing': {'name': 'Lab Wing',
              'brief': 'Secondary lab. A workstation glows. The specimen case was broken from inside.',
              'description': 'You are in the Lab Wing.\n'
                             'A secondary research space — clinical, smaller than the basement.\n'
                             'Steel cabinets line the walls. A workstation glows on backup power.\n'
                             'A glass specimen case on the central table — broken open from inside.\n'
                             'The air is colder here. Wrong cold.',
              'exits': {'west': 'basement'},
              'locked_exits': {},
              'items': {'medical file': 'A sealed file, red-taped. Your name is on the outside.',
                        'sample case': "A cracked specimen container. 'Subject 01 — Baseline.'"},
              'objects': {'workstation': 'Terminal on backup power. Screen shows a log entry:\n'
                                         "  'Subject 01 — status: AWOL.\n"
                                         '   Last reading: off-chart neural activity.\n'
                                         "   Recommend immediate containment if located.'\n"
                                         "A camera feed: four rooms. Three dark. One isn't.\n"
                                         'The Quarantine Room. Something moves in the corner.',
                          'specimen case': 'Reinforced glass — designed to hold biohazardous material.\n'
                                           'Something broke out. The edges are pushed outward.\n'
                                           'Bloodstains on the table. Old ones and new ones.\n'
                                           "Label: 'Subject 01 — Baseline Sample.'",
                          'cabinets': 'Most sealed with biohazard locks. One stands open — emptied.\n'
                                      'On the shelf inside, scratched into the metal:\n'
                                      "'He knows you're coming.'",
                          'camera feed': 'Four split-screen feeds. Three dark.\n'
                                         'Quarantine Room: something in the corner. Not moving.\n'
                                         'Waiting. The timestamp reads 8 weeks ago. Looping.'}}}
