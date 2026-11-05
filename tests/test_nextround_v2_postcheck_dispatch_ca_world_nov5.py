"""Next round v2 C13 (Brandon's 10 answers, item 2: 'Yes, go with your picks', relayed via Super 8:55 AM CST Nov 5): a bot-started
Canada or world key run dispatches 'KPC key check (after a key build)', as the US key does (Nov 5 hotfix). On top of Part 2 (C1's
chain jobs make bot-started Canada / world runs common). Workflow files only: no rules hash moves; no cron; actions: write only in the
new job."""
import pathlib
import yaml

W = pathlib.Path(__file__).resolve().parent.parent / '.github' / 'workflows'


def _y(f):
    y = yaml.safe_load(open(W / f, encoding='utf-8'))
    return y, (y.get('on') or y.get(True) or {})


def test_ca_and_world_dispatch_the_post_key_check():
    for f, key, needs in (('kpc-ca-key.yml', 'ca', ['run']), ('kpc-world-key.yml', 'world', ['plan', 'join'])):
        y, _ = _y(f)
        j = y['jobs']['postcheck']
        assert j['needs'] == needs and "github.triggering_actor == 'github-actions[bot]'" in j['if'] and 'always()' in j['if']
        assert j['permissions'] == {'actions': 'write', 'contents': 'read'}
        run = ' '.join(str(s.get('run')) for s in j['steps'])
        assert f'gh workflow run kpc-key-postcheck.yml -R "$GITHUB_REPOSITORY" --ref main -f key={key}' in run and 'kpc-hidden.txt' in run
    assert "needs.run.outputs.skip != '1'" in _y('kpc-ca-key.yml')[0]['jobs']['postcheck']['if']        # a skipped Canada start built nothing
    assert "needs.join.result == 'success'" in _y('kpc-world-key.yml')[0]['jobs']['postcheck']['if']


def test_person_runs_still_use_workflow_run_and_no_cron_added():
    y, on = _y('kpc-key-postcheck.yml')
    assert set(on['workflow_run']['workflows']) == {'KPC US answer key', 'KPC Canada answer key', 'KPC world answer key'}
    assert 'schedule' not in on and set(on['workflow_dispatch']['inputs']) >= {'key'}
    assert _y('kpc-ca-key.yml')[0]['name'] == 'KPC Canada answer key' and _y('kpc-world-key.yml')[0]['name'] == 'KPC world answer key'


def test_actions_write_only_in_the_dispatch_jobs():
    for f, jobs in (('kpc-ca-key.yml', {'chain', 'postcheck'}), ('kpc-world-key.yml', {'postcheck'})):
        y, _ = _y(f)
        assert 'actions' not in (y.get('permissions') or {})
        assert {n for n, j in y['jobs'].items() if (j.get('permissions') or {}).get('actions') == 'write'} == jobs, f
