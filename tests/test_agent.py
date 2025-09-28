from agents.local_agent.agent import decide
def test_local_agent_schema():
    d=decide({"test":True})
    assert "validator" in d and "params" in d and isinstance(d["params"], dict)
    assert {"alpha","threshold","window"}.issubset(d["params"].keys())
