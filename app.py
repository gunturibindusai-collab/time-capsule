from __future__ import annotations
import difflib, json, sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.version_manager import (new_capsule, add_version, reconstruct_version,
    storage_stats, save_capsule, load_capsule, capsule_archive_bytes, validate_capsule, CapsuleError)

DATA_DIR = ROOT / ".time_capsule_data"
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Time Capsule", page_icon="◷", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.035em; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1320px; }
[data-testid="stMetric"] { border: 1px solid #e5e7eb; padding: 16px 18px; border-radius: 14px; background: #fff; }
[data-testid="stSidebar"] { border-right: 1px solid #e5e7eb; }
.tc-eyebrow { color:#64748b; font-size:.76rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; }
.tc-sub { color:#64748b; margin-top:-.5rem; }
.tc-card { border:1px solid #e5e7eb; border-radius:16px; padding:18px 20px; background:#fff; }
.tc-pill { display:inline-block; border-radius:999px; padding:4px 10px; font-size:12px; background:#f1f5f9; color:#334155; font-weight:600; }
hr { border-color:#e5e7eb; }
</style>
""", unsafe_allow_html=True)

# --- persistence helpers ---
def all_capsules():
    out=[]
    for p in DATA_DIR.glob("*.json"):
        try:
            c=load_capsule(p); out.append((p,c))
        except Exception:
            continue
    return sorted(out, key=lambda x: x[1].get("created_at", ""), reverse=True)

def persist(c):
    save_capsule(c, DATA_DIR)
    st.session_state.active_capsule_id = c["id"]

def get_active():
    entries=all_capsules()
    active=st.session_state.get("active_capsule_id")
    for p,c in entries:
        if c["id"]==active:
            return p,c
    if entries:
        st.session_state.active_capsule_id=entries[0][1]["id"]
        return entries[0]
    return None,None

def fmt_bytes(n):
    n=float(n)
    for unit in ("B","KB","MB","GB"):
        if n < 1024 or unit == "GB":
            return f"{n:,.0f} {unit}" if unit == "B" else f"{n:,.2f} {unit}"
        n/=1024

def load_demo():
    return ("# Time Capsule demo project\n\n" 
            "def greet(name):\n"
            "    message = f\"Hello, {name}!\"\n"
            "    print(message)\n\n"
            "if __name__ == \"__main__\":\n"
            "    greet(\"world\")\n")


def load_version_callback(capsule, version_index):
    """Run before Streamlit rebuilds widgets, so editor state can be changed safely."""
    try:
        st.session_state["working_editor"] = reconstruct_version(capsule, version_index)
        st.session_state["editor_capsule_id"] = capsule["id"]
        st.session_state["editor_dirty"] = True
        st.session_state.pop("editor_action_error", None)
    except Exception as exc:
        st.session_state["editor_action_error"] = f"Could not load version: {exc}"

def reset_editor_callback(capsule_id, latest_text):
    """Reset to the latest snapshot (or starter example) before widget creation."""
    st.session_state["working_editor"] = latest_text
    st.session_state["editor_capsule_id"] = capsule_id
    st.session_state["editor_dirty"] = False
    st.session_state.pop("editor_action_error", None)

with st.sidebar:
    st.markdown("# ◷ Time Capsule")
    st.caption("Version history, without the storage bloat.")
    st.divider()
    st.markdown("**WORKSPACE**")
    entries=all_capsules()
    labels={f"{c['name']} · {len(c.get('versions',[]))} versions": c["id"] for _,c in entries}
    active_path, active = get_active()
    if entries:
        active_label=next((label for label, cid in labels.items() if active and cid==active["id"]), list(labels)[0])
        chosen=st.selectbox("Your capsules", list(labels.keys()), index=list(labels.keys()).index(active_label), label_visibility="collapsed")
        st.session_state.active_capsule_id=labels[chosen]
        active_path, active=get_active()
    else:
        st.info("Create your first capsule to begin.")
    with st.expander("＋ New capsule", expanded=not bool(entries)):
        new_name=st.text_input("Project name", value="My project", key="new_project_name")
        new_filename=st.text_input("Tracked filename", value="notes.py", key="new_filename")
        if st.button("Create capsule", use_container_width=True, type="primary"):
            if not new_name.strip() or not new_filename.strip():
                st.error("Add a project name and filename.")
            else:
                c=new_capsule(new_name, Path(new_filename).name)
                persist(c); st.rerun()
    st.divider()
    st.markdown("**PORTABILITY**")
    import_file=st.file_uploader("Import a capsule archive (.json)", type=["json"], key="import_capsule")
    if import_file is not None and st.button("Import archive", use_container_width=True):
        try:
            imported=json.loads(import_file.getvalue().decode("utf-8")); validate_capsule(imported)
            # Give imported capsule a fresh local ID to avoid overwriting a different workspace item.
            imported["id"] = __import__("uuid").uuid4().hex
            persist(imported); st.success("Capsule imported."); st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")
    st.caption("Capsules are stored locally in this app folder. Export backups regularly.")

st.markdown('<div class="tc-eyebrow">LOCAL VERSION CONTROL · DELTA COMPRESSION</div>', unsafe_allow_html=True)
st.title("Time Capsule")
st.markdown('<p class="tc-sub">Every version remembered. Less space wasted.</p>', unsafe_allow_html=True)

if active is None:
    st.markdown("### Start your first capsule")
    st.write("Create a capsule from the sidebar, then save snapshots as your file evolves.")
    st.stop()

stats=storage_stats(active)
versions=active.get("versions", [])
col_a,col_b,col_c,col_d=st.columns(4)
col_a.metric("Versions saved", stats["version_count"])
col_b.metric("Delta storage", fmt_bytes(stats["actual_bytes"]))
col_c.metric("Full-copy baseline", fmt_bytes(stats["full_copy_bytes"]))
if stats["full_copy_bytes"]:
    col_d.metric("Storage reduction", f"{stats['saved_percent']:.1f}%", help="Compared with independently zlib-compressing every full version. Negative means deltas used more space.")
else:
    col_d.metric("Storage reduction", "—")

if not versions:
    st.info("Your capsule is ready. Add the first snapshot below. The first snapshot becomes the compressed baseline.")

left, right = st.columns([1.2, 0.8], gap="large")
with left:
    st.subheader("Create a snapshot")
    st.caption(f"Tracking: **{active.get('filename','untitled.txt')}** · Capsule: **{active.get('name','Untitled')}**")
    latest_text=""
    if versions:
        try: latest_text=reconstruct_version(active, len(versions)-1)
        except Exception as e: st.error(str(e))
    uploaded=st.file_uploader("Load a text file into the editor", type=["txt","py","md","json","csv","html","css","js","yaml","yml","toml","xml","sql"], key="working_upload")
    if uploaded is not None and st.session_state.get("last_uploaded_name") != uploaded.name:
        try:
            loaded_text = uploaded.getvalue().decode("utf-8")
            st.session_state.pending_editor = loaded_text
            st.session_state.last_uploaded_name = uploaded.name
            st.session_state.uploaded_filename = uploaded.name
        except UnicodeDecodeError:
            st.error("This file is not valid UTF-8 text. Binary files are not supported in this MVP.")
    # Apply navigation/editor changes before the text_area widget is created.
    # Streamlit forbids changing a widget's keyed state after instantiation.
    pending = st.session_state.pop("pending_editor", None)
    if pending is not None:
        st.session_state["working_editor"] = pending
        st.session_state["editor_capsule_id"] = active["id"]
        st.session_state["editor_dirty"] = pending != latest_text

    if ("working_editor" not in st.session_state
            or st.session_state.get("editor_capsule_id") != active["id"]):
        st.session_state["working_editor"] = latest_text if versions else load_demo()
        st.session_state["editor_capsule_id"] = active["id"]
        st.session_state["editor_dirty"] = False
    content=st.text_area("Working content", key="working_editor", height=330, label_visibility="collapsed", placeholder="Paste or type your text here…")
    st.session_state.editor_dirty = content != latest_text
    if st.session_state.pop("clear_snapshot_label", False):
        # Widget state can only be changed before instantiating the widget.
        st.session_state.snapshot_label = ""
    if st.session_state.get("editor_action_error"):
        st.error(st.session_state.pop("editor_action_error"))
    label=st.text_input("Snapshot label", placeholder="e.g. Added validation and error handling", key="snapshot_label")
    save_col, reset_col=st.columns([1,1])
    with save_col:
        if st.button("Save snapshot", type="primary", use_container_width=True):
            try:
                add_version(active, content, label)
                persist(active)
                st.session_state.editor_dirty=False
                st.session_state.clear_snapshot_label = True
                st.success("Snapshot saved and integrity hash recorded.")
                st.rerun()
            except Exception as e: st.error(f"Could not save snapshot: {e}")
    with reset_col:
        st.button(
            "Reset editor to latest", use_container_width=True,
            on_click=reset_editor_callback,
            args=(active["id"], latest_text if versions else load_demo()),
        )

with right:
    st.subheader("Version timeline")
    if not versions:
        st.markdown('<div class="tc-card"><strong>No history yet</strong><br/><span style="color:#64748b">Your snapshots will appear here.</span></div>', unsafe_allow_html=True)
    else:
        for idx, v in reversed(list(enumerate(versions))):
            is_latest=idx==len(versions)-1
            with st.container(border=True):
                r1,r2=st.columns([0.72,0.28])
                r1.markdown(f"**v{v['number']} · {v.get('label','Version')}**")
                r1.caption(v.get("created_at", "") + (" · Latest" if is_latest else ""))
                r2.markdown(f"`{v['kind']}`")
                r2.caption(fmt_bytes(v.get("payload_bytes",0)))
                st.button(
                    "Load into editor", key=f"load_{v['id']}", use_container_width=True,
                    on_click=load_version_callback, args=(active, idx),
                )
    st.markdown(" ")
    if versions:
        st.download_button("Export capsule archive", data=capsule_archive_bytes(active), file_name=f"{active['name'].replace(' ','_')}_time_capsule.json", mime="application/json", use_container_width=True)
        st.caption("Includes compressed payloads, version labels, metadata and hashes.")

st.divider()
st.subheader("Compare versions")
if len(versions) < 2:
    st.info("Save at least two snapshots to inspect their differences.")
else:
    opts=[f"v{v['number']} · {v.get('label','Version')}" for v in versions]
    ca,cb=st.columns(2)
    with ca:
        old_idx=st.selectbox("Older version", range(len(versions)), index=max(0,len(versions)-2), key="compare_old_idx", format_func=lambda i: opts[i])
    with cb:
        new_idx=st.selectbox("Newer version", range(len(versions)), index=len(versions)-1, key="compare_new_idx", format_func=lambda i: opts[i])
    if old_idx==new_idx:
        st.warning("Choose two different versions to compare.")
    else:
        try:
            old_text=reconstruct_version(active,old_idx); new_text=reconstruct_version(active,new_idx)
            added=sum(1 for line in difflib.ndiff(old_text.splitlines(),new_text.splitlines()) if line.startswith("+ "))
            removed=sum(1 for line in difflib.ndiff(old_text.splitlines(),new_text.splitlines()) if line.startswith("- "))
            unchanged=max(0,len(old_text.splitlines())-removed)
            m1,m2,m3=st.columns(3); m1.metric("Lines added",added); m2.metric("Lines removed",removed); m3.metric("Older version size",fmt_bytes(len(old_text.encode('utf-8'))))
            diff="\n".join(difflib.unified_diff(
                old_text.splitlines(), new_text.splitlines(),
                fromfile=opts[old_idx], tofile=opts[new_idx], lineterm=""
            ))
            st.code(diff or "No differences — these versions contain identical text.", language="diff", line_numbers=False)
            d1,d2=st.columns(2)
            with d1: st.download_button("Download selected older version",old_text.encode("utf-8"),file_name=f"{Path(active['filename']).stem}_v{old_idx+1}{Path(active['filename']).suffix}",mime="text/plain",use_container_width=True)
            with d2: st.download_button("Download selected newer version",new_text.encode("utf-8"),file_name=f"{Path(active['filename']).stem}_v{new_idx+1}{Path(active['filename']).suffix}",mime="text/plain",use_container_width=True)
        except Exception as e: st.error(f"Comparison failed: {e}")

with st.expander("How the compression works"):
    st.markdown("""
    1. **Baseline:** the first snapshot is compressed with zlib.
    2. **Delta:** each later snapshot is compared with the previous reconstructed version. A compact operation stream records unchanged spans and inserted, deleted or replaced text.
    3. **Compression:** that operation stream is compressed with zlib and stored instead of a complete new copy.
    4. **Recovery:** Time Capsule replays deltas in order to reconstruct the requested version.
    5. **Integrity:** SHA-256 verifies each reconstructed snapshot against its recorded digest.

    **Metric note:** the comparison is against independently zlib-compressed full versions, not raw uncompressed text. Delta storage can be larger when versions change substantially; the dashboard reports the measured result rather than hiding it.
    """)
st.caption("Time Capsule MVP · Local-first storage · UTF-8 text only · Keep exported backups of important work.")
