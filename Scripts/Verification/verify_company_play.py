"""In-process listen/client Company acceptance. No direct client-state writes.
Owned requests run with editor Python's server-RPC bypass disabled by native helpers.
Companies are session-only and disappear on Stop Play.
"""
import unreal,json,time
from pathlib import Path
lib=unreal.EWEditorVerificationLibrary
worlds=lib.get_play_worlds()
assert len(worlds)==2
pcs=[unreal.GameplayStatics.get_player_controller(w,0) for w in worlds]
client=next(c for c in pcs if not c.has_authority())
host=next(c for c in pcs if c.has_authority())
server=worlds[pcs.index(host)]
def pid(pc): return json.loads(unreal.ToolsetLibrary.get_object_properties(pc.get_editor_property('PlayerState'),['PlayerId']))['PlayerId']
client_id=pid(client); host_id=pid(host)
remote=next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server,unreal.EWPlayerController) if pid(p)==client_id)
cc=client.get_company_component(); sc=remote.get_company_component(); hc=host.get_company_component()
A=unreal.EWCompanyAction; P=unreal.EWCompanyOwnership
checks=[]; phase=0; next_at=time.monotonic()+1; handle=None
def command(pc,action,text='',target=-1): assert lib.send_verification_company_command(pc,action,text,target)
def snapshot(c): return c.get_company()
def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(),'CompanyPlayResult.json').write_text(json.dumps({'success':error is None,'checks':checks,'error':error},indent=2))
def tick(delta):
    global phase,next_at
    if time.monotonic()<next_at:return
    next_at=time.monotonic()+2
    try:
        if phase==0: command(client,A.CREATE,'Sea Wolves')
        elif phase==1:
            assert snapshot(sc).name=='Sea Wolves' and snapshot(cc).name=='Sea Wolves'
            assert snapshot(cc).owner_id==client_id and len(snapshot(cc).members)==1
            checks.append('Client creates Company through owned RPC; authoritative owner and roster replicate')
            command(client,A.INVITE,target=host_id)
        elif phase==2:
            assert hc.get_invitation_name()=='Sea Wolves'
            assert len(snapshot(sc).members)==1
            checks.append('Invitation targets connected player without joining them automatically')
            command(host,A.ACCEPT_INVITE)
        elif phase==3:
            assert len(snapshot(cc).members)==2 and snapshot(hc).name=='Sea Wolves'
            checks.append('Accepted invitation joins the same authoritative Company and replicates both rosters')
            command(host,A.RENAME,'Stolen Name')
        elif phase==4:
            assert snapshot(sc).name=='Sea Wolves'
            checks.append('Ordinary member cannot rename Company')
            assert lib.send_verification_company_policy(host,0,P.COMPANY)
        elif phase==5:
            assert snapshot(sc).ships==P.PERSONAL
            checks.append('Ordinary member cannot change ownership policy')
            command(client,A.PROMOTE,target=host_id)
        elif phase==6:
            assert next(m for m in snapshot(cc).members if m.player_id==host_id).manager
            checks.append('Owner promotion to prototype Manager role replicates')
            command(host,A.RENAME,'Manager Rename')
        elif phase==7:
            assert snapshot(cc).name=='Sea Wolves'
            checks.append('Manager cannot bypass owner-only renaming')
            assert lib.send_verification_company_policy(client,0,P.PERSONAL_SHARED)
        elif phase==8:
            assert snapshot(hc).ships==P.PERSONAL_SHARED
            checks.append('Owner-selected shared-access policy replicates without transferring world assets')
            command(client,A.LEAVE)
        elif phase==9:
            assert len(snapshot(cc).members)==2 and snapshot(cc).owner_id==client_id
            checks.append('Owner cannot orphan an occupied Company by leaving')
            command(client,A.TRANSFER_OWNER,target=host_id)
        elif phase==10:
            assert snapshot(cc).owner_id==host_id and snapshot(hc).owner_id==host_id
            checks.append('Explicit leadership transfer changes authoritative owner on both peers')
            command(client,A.RENAME,'Former Owner Rename')
        elif phase==11:
            assert snapshot(hc).name=='Sea Wolves'
            checks.append('Former owner loses renaming authority immediately')
            command(host,A.RENAME,'Harbor Wolves')
        elif phase==12:
            assert snapshot(cc).name=='Harbor Wolves'
            checks.append('New owner can rename Company')
            command(client,A.LEAVE)
        elif phase==13:
            assert len(snapshot(cc).members)==0 and len(snapshot(hc).members)==1
            checks.append('Member departure clears only their membership and updates remaining roster')
            command(client,A.CREATE,'harbor wolves')
        elif phase==14:
            assert len(snapshot(cc).members)==0
            checks.append('Case-insensitive duplicate company name rejected')
            command(client,A.CREATE,'Free Sailors')
        elif phase==15:
            assert snapshot(cc).name=='Free Sailors' and snapshot(hc).name=='Harbor Wolves'
            checks.append('Two independent Companies coexist without cross-membership')
            finish(); return
        phase+=1
    except Exception as e: finish(repr(e))
handle=unreal.register_slate_post_tick_callback(tick)
