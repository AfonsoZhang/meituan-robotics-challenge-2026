# Browser verification scope

Native ROS fixtures supplied all camera/detection/planner/tool observations. RGB screenshot shows target fixture-battery-1, Attached + verified=false + evidence 1, independent mounting unconfirmed, test-lift verified and seated unprovided. Planner screenshot retains injected EXCEEDS_STATE_WATCHDOG. Follow-up DOM capture records Cancel ACK accepted, native ABORTED/520, while Stop Confirmed remains unconfirmed.

The first composite flow captured immediately after a pause/resume while the HTTP snapshot was pending; its `active` object is explicitly unknown and is NOT claimed as the positive evidence. The later RGB screenshot and p1-browser-observations.json are the positive observations. Those are separate from the source fixture ROS suite.

Chrome document.visibilityState was hidden. rAF-based wait/click stability timed out; keyboard activation did not submit while freshness was expired. A normal window restore via the extension's CDP session was disallowed; no bypass was attempted. Final checks used DOM .click() with enabled button checks and the existing Pause/Resume UI to request fresh snapshots; no JavaScript state or backend snapshot was injected. This does not claim foreground pointer/keyboard coverage.

Temporary Docker-exec relay initially returned 502 for static assets, causing P1 undefined errors; later relay serialized exec and cached only successfully fetched static bytes. These harness failures and first layout overflow are retained. Final three views at 320/390/768/1440 had no document overflow. The detection table scrolls within its own container.

The final small P1 render change preserves opened pose details within the same session/source during ordinary fresh sample refresh; it does not preserve them across stale/pause clearing. Node semantic regression reran afterward; interactive detail persistence was not separately asserted in the hidden browser.
