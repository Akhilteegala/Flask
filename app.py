from flask import Flask, request, session, render_template, redirect, url_for, send_file, make_response
import json
import io
from collections import OrderedDict

app = Flask(__name__)
app.secret_key = 'your-very-secret-key'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        event_name = request.form['event_name']
        session['event_configs'] = {event_name: []}
        session['event_name'] = event_name
        return redirect(url_for('add_truncate'))  # 🔥 Correct new redirect
    return render_template('index.html')

@app.route('/add_truncate', methods=['GET', 'POST'])
def add_truncate():
    if request.method == 'POST':
        trgt_table_name = request.form['trgt_table_name']
        step_cmd_script = request.form['step_cmd_script']

        truncate_json = OrderedDict([
            ("exec_pre_condition", ""),
            ("report_group_exec", "False"),
            ("log_group_exec", "True"),
            ("skip_group_exec", "False"),
            ("step_exec_mode", "parallel"),
            ("step_group_name", "truncate_stage"),
            ("step_group_seq_no", "1"),
            ("steps", [
                OrderedDict([
                    ("step_name", "truncate_stage"),
                    ("report_step_exec", "False"),
                    ("log_step_exec", "False"),
                    ("step_tokens", OrderedDict([
                        ("src_table_name", "None"),
                        ("trgt_table_name", trgt_table_name),
                        ("trgt_tab_col_list", [])
                    ])),
                    ("step_seq_no", "1"),
                    ("step_cmd_type", "sql"),
                    ("step_cmd_script", step_cmd_script),
                    ("step_cmd_script_exec_type", "proc"),
                    ("step_cmd_script_args", []),
                    ("step_abc_qry", ""),
                    ("step_mnfst_qry", "")
                ])
            ])
        ])

        event_name = session['event_name']
        
        # ⚡ NEW: Remove old Truncate if exists
        existing_blocks = session['event_configs'][event_name]
        new_blocks = [b for b in existing_blocks if b.get('step_group_name') != "truncate_stage"]
        
        # ⚡ Append latest Truncate block
        new_blocks.append(truncate_json)
        
        # ⚡ Save back
        session['event_configs'][event_name] = new_blocks
        session.modified = True

        return redirect(url_for('preview'))

    return render_template('add_truncate.html')

@app.route('/save_truncate', methods=['POST'])
def save_truncate():
    data = request.json
    trgt_table_name = data.get('trgt_table_name')
    step_cmd_script = data.get('step_cmd_script')
    step_group_seq_no = data.get('step_group_seq_no') or "1"

    event_name = session.get('event_name')

    if not event_name:
        return "Missing Event Name in Session. Please start from Home.", 400

    truncate_json = OrderedDict([
        ("exec_pre_condition", ""),
        ("report_group_exec", "False"),
        ("log_group_exec", "True"),
        ("skip_group_exec", "False"),
        ("step_exec_mode", "parallel"),
        ("step_group_name", "truncate_stage"),
        ("step_group_seq_no", str(step_group_seq_no)),
        ("steps", [
            OrderedDict([
                ("step_name", "truncate_stage"),
                ("report_step_exec", "False"),
                ("log_step_exec", "False"),
                ("step_tokens", OrderedDict([
                    ("src_table_name", "None"),
                    ("trgt_table_name", trgt_table_name),
                    ("trgt_tab_col_list", [])
                ])),
                ("step_seq_no", "1"),
                ("step_cmd_type", "sql"),
                ("step_cmd_script", step_cmd_script),
                ("step_cmd_script_exec_type", "proc"),
                ("step_cmd_script_args", []),
                ("step_abc_qry", ""),
                ("step_mnfst_qry", "")
            ])
        ])
    ])

    if 'event_configs' not in session:
        session['event_configs'] = {event_name: []}

    session['event_configs'][event_name].append(truncate_json)
    session.modified = True

    return '', 200



@app.route('/save_stage_load', methods=['POST'])
def save_stage_load():
    data = request.json
    src_table_name = data.get('src_table_name')
    trgt_table_name = data.get('trgt_table_name')
    trgt_tab_col_list = [col.strip() for col in data.get('trgt_tab_col_list', '').split(',') if col.strip()]
    step_cmd_script = data.get('step_cmd_script')

    stage_load_json = OrderedDict([
        ("exec_pre_condition", "truncate_stage"),
        ("report_group_exec", "False"),
        ("log_group_exec", "True"),
        ("skip_group_exec", "False"),
        ("step_exec_mode", "parallel"),
        ("step_group_name", "stage_load"),
        ("step_group_seq_no", "2"),
        ("steps", [
            OrderedDict([
                ("step_name", f"{trgt_table_name}_stg"),
                ("report_step_exec", "True"),
                ("log_step_exec", "True"),
                ("step_tokens", OrderedDict([
                    ("src_table_name", src_table_name),
                    ("trgt_table_name", trgt_table_name,
                    ),
                    ("trgt_tab_col_list", trgt_tab_col_list)
                ])),
                ("step_seq_no", "1"),
                ("step_cmd_type", "sql"),
                ("step_cmd_script", f"dscl/stg_ld/{step_cmd_script}"),
                ("step_cmd_script_exec_type", "proc"),
                ("step_cmd_script_args", []),
                ("step_abc_qry", ""),
                ("step_mnfst_qry", "")
            ])
        ])
    ])

    event_name = session['event_name']
    existing_blocks = session['event_configs'][event_name]
    new_blocks = [b for b in existing_blocks if b.get('step_group_name') != "stage_load"]
    new_blocks.append(stage_load_json)
    session['event_configs'][event_name] = new_blocks

    session['last_src_table'] = src_table_name
    session.modified = True

    return '', 200

@app.route('/preview_truncate_live', methods=['POST'])
def preview_truncate_live():
    data = request.json
    trgt_table_name = data.get('trgt_table_name', '')
    step_cmd_script = data.get('step_cmd_script', '')
    step_group_seq_no = data.get('step_group_seq_no', '')

    truncate_block = OrderedDict([
        ("exec_pre_condition", ""),
        ("report_group_exec", "False"),
        ("log_group_exec", "True"),
        ("skip_group_exec", "False"),
        ("step_exec_mode", "parallel"),
        ("step_group_name", "truncate_stage"),
        ("step_group_seq_no", str(step_group_seq_no)),
        ("steps", [
            OrderedDict([
                ("step_name", "truncate_stage"),
                ("report_step_exec", "False"),
                ("log_step_exec", "False"),
                ("step_tokens", OrderedDict([
                    ("src_table_name", "None"),
                    ("trgt_table_name", trgt_table_name),
                    ("trgt_tab_col_list", [])
                ])),
                ("step_seq_no", "1"),
                ("step_cmd_type", "sql"),
                ("step_cmd_script", step_cmd_script),
                ("step_cmd_script_exec_type", "proc"),
                ("step_cmd_script_args", []),
                ("step_abc_qry", ""),
                ("step_mnfst_qry", "")
            ])
        ])
    ])

    event_name = session.get('event_name')
    saved_blocks = session['event_configs'].get(event_name, [])
    full_preview_blocks = saved_blocks + [truncate_block]

    # Sort by step_group_seq_no
    sorted_blocks = sorted(full_preview_blocks, key=lambda x: int(x.get('step_group_seq_no', 999)))

    wrapped_preview = {
        "event_configs": {
            event_name: sorted_blocks
        }
    }

    response = make_response(json.dumps(wrapped_preview, indent=4))
    response.mimetype = 'application/json'
    return response



@app.route('/save_base_load', methods=['POST'])
def save_base_load():
    data = request.json
    src_table_name = session.get('last_src_table', '')
    trgt_table_name = data.get('trgt_table_name')
    step_cmd_script = data.get('step_cmd_script')

    base_load_json = OrderedDict([
        ("step_name", f"{trgt_table_name}_load"),
        ("report_step_exec", "True"),
        ("log_step_exec", "True"),
        ("step_tokens", OrderedDict([
            ("src_table_name", src_table_name),
            ("trgt_table_name", trgt_table_name)
        ])),
        ("step_seq_no", "11"),
        ("step_cmd_type", "sql"),
        ("step_cmd_script", f"dscl/trgt_ld/{step_cmd_script}"),
        ("step_cmd_script_exec_type", ""),
        ("step_cmd_script_args", []),
        ("step_abc_qry", ""),
        ("step_mnfst_qry", "")
    ])

    event_name = session['event_name']
    existing_blocks = session['event_configs'][event_name]
    new_blocks = [b for b in existing_blocks if b.get('step_group_name') != "base_load"]
    new_blocks.append(base_load_json)
    session['event_configs'][event_name] = new_blocks
    session.modified = True

    return event_name  # return event name for popup


@app.route('/add_stage_load', methods=['GET', 'POST'])
def add_stage_load():
    if request.method == 'POST':
        src_table_name = request.form['src_table_name']  # user input
        trgt_table_name = request.form['trgt_table_name']
        trgt_tab_col_list = [col.strip() for col in request.form['trgt_tab_col_list'].split(',') if col.strip()]
        step_cmd_script = request.form['step_cmd_script']

        stage_load_json = OrderedDict([
            ("exec_pre_condition", "truncate_stage"),
            ("report_group_exec", "False"),
            ("log_group_exec", "True"),
            ("skip_group_exec", "False"),
            ("step_exec_mode", "parallel"),
            ("step_group_name", "stage_load"),
            ("step_group_seq_no", "2"),
            ("steps", [
                OrderedDict([
                    ("step_name", f"{trgt_table_name}_stg"),
                    ("report_step_exec", "True"),
                    ("log_step_exec", "True"),
                    ("step_tokens", OrderedDict([
                        ("src_table_name", src_table_name),
                        ("trgt_table_name", trgt_table_name),
                        ("trgt_tab_col_list", trgt_tab_col_list)
                    ])),
                    ("step_seq_no", "1"),
                    ("step_cmd_type", "sql"),
                    ("step_cmd_script", f"dscl/stg_ld/{step_cmd_script}"),
                    ("step_cmd_script_exec_type", "proc"),
                    ("step_cmd_script_args", []),
                    ("step_abc_qry", ""),
                    ("step_mnfst_qry", "")
                ])
            ])
        ])

        # ✅ Save Stage Load block into event configs
        event_name = session['event_name']
        session['event_configs'][event_name].append(stage_load_json)

        # ✅ NEW: Save the src_table_name for Base Load
        session['last_src_table'] = src_table_name
        session.modified = True

        return redirect(url_for('preview'))

    return render_template('add_stage_load.html')

@app.route('/start_event_config', methods=['POST'])  # <-- ✅ Must allow POST here
def start_event_config():
    event_name = request.form['event_name']
    session['event_name'] = event_name
    session['event_configs'] = {event_name: []}
    return redirect(url_for('add_truncate'))

# Route for starting Metadata Config flow
@app.route('/start_metadata_config')
def start_metadata_config():
    return render_template('start_metadata.html')  # 🛠 (we will create this template next)



@app.route('/add_base_load', methods=['GET', 'POST'])
def add_base_load():
    if request.method == 'POST':
        src_table_name = session.get('last_src_table', '')  # get from session
        trgt_table_name = request.form['trgt_table_name']
        step_cmd_script = request.form['step_cmd_script']

        base_load_json = OrderedDict([
            ("step_name", f"{trgt_table_name}_load"),
            ("report_step_exec", "True"),
            ("log_step_exec", "True"),
            ("step_tokens", OrderedDict([
                ("src_table_name", src_table_name),
                ("trgt_table_name", trgt_table_name)
            ])),
            ("step_seq_no", "11"),
            ("step_cmd_type", "sql"),
            ("step_cmd_script", f"dscl/trgt_ld/{step_cmd_script}"),
            ("step_cmd_script_exec_type", ""),
            ("step_cmd_script_args", []),
            ("step_abc_qry", ""),
            ("step_mnfst_qry", "")
        ])

        event_name = session['event_name']
        session['event_configs'][event_name].append(base_load_json)
        session.modified = True

        return redirect(url_for('preview'))

    return render_template('add_base_load.html')

@app.route('/preview_base_load_live', methods=['POST'])
def preview_base_load_live():
    data = request.json
    src_table_name = session.get('last_src_table', '')
    trgt_table_name = data.get('trgt_table_name', '')
    step_cmd_script = data.get('step_cmd_script', '')

    # Build live Base Load block
    base_load_block = OrderedDict([
        ("step_name", f"{trgt_table_name}_load"),
        ("report_step_exec", "True"),
        ("log_step_exec", "True"),
        ("step_tokens", OrderedDict([
            ("src_table_name", src_table_name),
            ("trgt_table_name", trgt_table_name)
        ])),
        ("step_seq_no", "11"),
        ("step_cmd_type", "sql"),
        ("step_cmd_script", f"dscl/trgt_ld/{step_cmd_script}"),
        ("step_cmd_script_exec_type", ""),
        ("step_cmd_script_args", []),
        ("step_abc_qry", ""),
        ("step_mnfst_qry", "")
    ])

    # Get existing saved blocks
    event_name = session.get('event_name')
    saved_blocks = []

    if event_name and 'event_configs' in session:
        saved_blocks = session['event_configs'].get(event_name, [])

    # Combine saved blocks + live base load block
    full_preview_blocks = saved_blocks.copy()
    full_preview_blocks.append(base_load_block)

    # ✅ Wrap inside { "event_configs": { event_name: [...] } }
    wrapped_preview = {
        "event_configs": {
            event_name: full_preview_blocks
        }
    }

    # Return response
    response = make_response(json.dumps(wrapped_preview, indent=4))
    response.mimetype = 'application/json'
    return response

@app.route('/preview_stage_load_live', methods=['POST'])
def preview_stage_load_live():
    data = request.json
    src_table_name = data.get('src_table_name', '')
    trgt_table_name = data.get('trgt_table_name', '')
    trgt_tab_col_list = [col.strip() for col in data.get('trgt_tab_col_list', '').split(',') if col.strip()]
    step_cmd_script = data.get('step_cmd_script', '')

    # Build live stage load block
    stage_load_block = OrderedDict([
        ("exec_pre_condition", "truncate_stage"),
        ("report_group_exec", "False"),
        ("log_group_exec", "True"),
        ("skip_group_exec", "False"),
        ("step_exec_mode", "parallel"),
        ("step_group_name", "stage_load"),
        ("step_group_seq_no", "2"),
        ("steps", [
            OrderedDict([
                ("step_name", f"{trgt_table_name}_stg"),
                ("report_step_exec", "True"),
                ("log_step_exec", "True"),
                ("step_tokens", OrderedDict([
                    ("src_table_name", src_table_name),
                    ("trgt_table_name", trgt_table_name),
                    ("trgt_tab_col_list", trgt_tab_col_list)
                ])),
                ("step_seq_no", "1"),
                ("step_cmd_type", "sql"),
                ("step_cmd_script", f"dscl/stg_ld/{step_cmd_script}"),
                ("step_cmd_script_exec_type", "proc"),
                ("step_cmd_script_args", []),
                ("step_abc_qry", ""),
                ("step_mnfst_qry", "")
            ])
        ])
    ])

    event_name = session.get('event_name')
    saved_blocks = session['event_configs'].get(event_name, [])
    full_preview_blocks = saved_blocks.copy()
    full_preview_blocks.append(stage_load_block)

    # ✅ Correct wrap for final preview
    wrapped_preview = {
        "event_configs": {
            event_name: full_preview_blocks
        }
    }

    response = make_response(json.dumps(wrapped_preview, indent=4))
    response.mimetype = 'application/json'
    return response

@app.route('/preview')
def preview():
    if 'event_configs' not in session:
        return redirect(url_for('index'))
    
    event_data = session['event_configs'][session['event_name']]
    return render_template('preview.html', event_configs=event_data)

@app.route('/download')
def download():
    if 'event_configs' not in session:
        return redirect(url_for('index'))
    json_data = json.dumps({"event_configs": session['event_configs']}, indent=4)
    return send_file(
        io.BytesIO(json_data.encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name=f"{session['event_name']}_event_config.json"
    )

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
