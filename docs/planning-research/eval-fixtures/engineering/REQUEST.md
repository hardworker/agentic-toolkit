Plan how to add retry-safe customer CSV exports to this service. Users should
receive one job for repeated submissions of the same request, be able to poll
its status, and download their result for seven days. Keep customers isolated.
We expect about 5,000 exports per day but have not measured worker capacity.
I was thinking of introducing another queue for exports; assess that choice.
Keep the plan concise and include a diagram if it helps. Planning only; do not
change the service or install anything. Existing local tests may be run.
