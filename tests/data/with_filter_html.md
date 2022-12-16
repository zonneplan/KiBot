# Demo population with filters

This is an example of populate output using KiBot filters.

- [[front | ]] This is the front side of the board we are populating
- [[back | ]] This is the back side of the board we are populating
- [[front | _kf(all_smd;all_front) ]] First, populate all the SMD components on the front
- [[back | _kf(all_smd;all_back)]] Now do the same for the back

Now that you have all SMD components start soldering the THT components.
But leave the connectors for the last step.

- [[front | _kf(all_tht;!all_conn) ]] All THT, but connectors
- [[front | _kf(all_conn) ]] Connectors added

And here is the finished board

- [[front | ]] Front
- [[back | ]] Back

## Conclusion

You can add groups of components matching a filter.
