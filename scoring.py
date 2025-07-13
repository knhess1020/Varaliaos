import math

def cosine(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    return dot / (math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b))+1e-8)

def hybrid_score(sim: float, ts: float, now: float, decay_h: int = 24) -> float:
    age = max((now - ts) / 3600, 0.0)
    time_weight = math.exp(-age/decay_h)
    return 0.7*sim + 0.3*time_weight
