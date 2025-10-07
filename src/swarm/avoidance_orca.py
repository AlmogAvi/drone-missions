import rvo2
def orca_velocities(agents, radii=3.0, max_speed=10.0, dt=0.1):
    # agents: [(x,y,vx,vy), ...]
    sim = rvo2.PyRVOSimulator(dt, neighborDist=15, maxNeighbors=10,
                              timeHorizon=2.5, timeHorizonObst=2.5,
                              radius=radii, maxSpeed=max_speed)
    idx = [sim.addAgent((x,y)) for (x,y,_,_) in agents]
    for i,(x,y,vx,vy) in zip(idx, agents):
        sim.setAgentVelocity(i, (vx,vy))
        sim.setAgentPrefVelocity(i, (vx,vy))
    sim.doStep()
    return [sim.getAgentVelocity(i) for i in idx]
