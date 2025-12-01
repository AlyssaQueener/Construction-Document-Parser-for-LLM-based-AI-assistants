def display_comparison_view(ai_files_data, det_files_data):
    """Display AI vs Deterministic comparison for neighboring rooms"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("AI Method")
        if ai_files_data:
            ai_comparison = []
            for file_name, json_data in ai_files_data:
                stats = calculate_stats(json_data, 'drawing')
                ai_comparison.append({
                    'File': file_name,
                    'Overall Score': stats['overall_score'],
                    'Room Detection': stats['room_detection_score'],
                    'Adjacency F1': stats['adjacency_f1'],
                    'Precision': stats['adjacency_precision'],
                    'Recall': stats['adjacency_recall']
                })
            df_ai = pd.DataFrame(ai_comparison)
            
            def highlight_scores(val):
                if isinstance(val, (int, float)):
                    if val >= 9:
                        return 'background-color: #d1fae5'
                    elif val >= 7:
                        return 'background-color: #fef3c7'
                    elif val < 7 and val > 0:
                        return 'background-color: #fee2e2'
                return ''
            
            styled_df = df_ai.style.applymap(
                highlight_scores,
                subset=['Overall Score', 'Room Detection', 'Adjacency F1']
            )
            st.dataframe(styled_df, use_container_width=True)
            
            # Calculate averages
            st.markdown("**Averages:**")
            avg_col1, avg_col2, avg_col3 = st.columns(3)
            with avg_col1:
                st.metric("Avg Overall", f"{df_ai['Overall Score'].mean():.2f}")
            with avg_col2:
                st.metric("Avg Room Det.", f"{df_ai['Room Detection'].mean():.2f}")
            with avg_col3:
                st.metric("Avg Adj F1", f"{df_ai['Adjacency F1'].mean():.2f}")
        else:
            st.info("No AI method data available. Upload files in the 'Drawing - Neighboring (AI)' tab.")
    
    with col2:
        st.subheader("Deterministic Method")
        if det_files_data:
            det_comparison = []
            for file_name, json_data in det_files_data:
                stats = calculate_stats(json_data, 'drawing')
                det_comparison.append({
                    'File': file_name,
                    'Overall Score': stats['overall_score'],
                    'Room Detection': stats['room_detection_score'],
                    'Adjacency F1': stats['adjacency_f1'],
                    'Precision': stats['adjacency_precision'],
                    'Recall': stats['adjacency_recall']
                })
            df_det = pd.DataFrame(det_comparison)
            
            def highlight_scores(val):
                if isinstance(val, (int, float)):
                    if val >= 9:
                        return 'background-color: #d1fae5'
                    elif val >= 7:
                        return 'background-color: #fef3c7'
                    elif val < 7 and val > 0:
                        return 'background-color: #fee2e2'
                return ''
            
            styled_df = df_det.style.applymap(
                highlight_scores,
                subset=['Overall Score', 'Room Detection', 'Adjacency F1']
            )
            st.dataframe(styled_df, use_container_width=True)
            
            # Calculate averages
            st.markdown("**Averages:**")
            avg_col1, avg_col2, avg_col3 = st.columns(3)
            with avg_col1:
                st.metric("Avg Overall", f"{df_det['Overall Score'].mean():.2f}")
            with avg_col2:
                st.metric("Avg Room Det.", f"{df_det['Room Detection'].mean():.2f}")
            with avg_col3:
                st.metric("Avg Adj F1", f"{df_det['Adjacency F1'].mean():.2f}")
        else:
            st.info("No Deterministic method data available. Upload files in the 'Drawing - Neighboring (Deterministic)' tab.")

def display_room_analysis(file_name, json_data):
    """Display detailed room analysis for drawing parsers"""
    room_analysis = json_data.get('room_analysis', {})
    
    if not room_analysis:
        st.info("No room analysis data available")
        return
    
    st.subheader(f"Room Analysis - {file_name}")
    
    # Create columns for room cards
    cols = st.columns(3)
    
    for idx, (room_name, data) in enumerate(room_analysis.items()):
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"**{room_name}**")
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("F1", f"{data['f1']:.2f}")
                with col2:
                    st.metric("Precision", f"{data['precision']:.2f}")
                with col3:
                    st.metric("Recall", f"{data['recall']:.2f}")
                
                # False positives
                if data.get('false_positives'):
                    st.markdown("🔴 **False Positives:**")
                    for fp in data['false_positives']:
                        st.markdown(f"- {fp}")
                
                # False negatives
                if data.get('false_negatives'):
                    st.markdown("🟠 **False Negatives:**")
                    for fn in data['false_negatives']:
                        st.markdown(f"- {fn}")
                
                # Note
                if data.get('note'):
                    st.info(data['note'])
                
                st.divider()
import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Validation JSON Comparison Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'files' not in st.session_state:
    st.session_state.files = {
        'financial': [],
        'gantt': [],
        'drawing_titleblock': [],
        'drawing_neighboring_ai': [],
        'drawing_neighboring_deterministic': [],
        'drawing_fullplan_ai': []
    }

def load_json_file(uploaded_file):
    """Load and parse JSON file"""
    try:
        return json.load(uploaded_file)
    except Exception as e:
        st.error(f"Error loading {uploaded_file.name}: {str(e)}")
        return None

def calculate_stats(json_data, parser_type):
    """Calculate statistics from JSON data based on parser type"""
    if not json_data:
        return None
    
    if parser_type == 'financial':
        # Financial parser structure
        section_analysis = json_data.get('section_analysis', [])
        total_items = sum(len(section.get('item_analysis', [])) for section in section_analysis)
        
        # Calculate average scores across all items
        all_scores = []
        for section in section_analysis:
            for item in section.get('item_analysis', []):
                match_scores = item.get('match_scores', {})
                if match_scores:
                    avg_score = sum(match_scores.values()) / len(match_scores)
                    all_scores.append(avg_score)
        
        avg_item_score = (sum(all_scores) / len(all_scores) * 10) if all_scores else 0
        
        return {
            'overall_score': json_data.get('overall_score', 0),
            'completeness': json_data.get('completeness', 0),
            'accuracy': json_data.get('accuracy', 0),
            'total_sections': len(section_analysis),
            'total_items': total_items,
            'avg_item_score': avg_item_score,
            'confidence': json_data.get('confidence_calibration', 'N/A')
        }
    
    elif parser_type == 'gantt':
        # Gantt parser structure
        summary = json_data.get('summary', {})
        field_evals = json_data.get('field_evaluations', [])
        
        # Calculate average field scores
        all_field_scores = []
        for evaluation in field_evals:
            field_scores = evaluation.get('field_scores', {})
            if field_scores:
                all_field_scores.extend(field_scores.values())
        
        avg_field_score = (sum(all_field_scores) / len(all_field_scores) * 10) if all_field_scores else 0
        
        return {
            'overall_score': json_data.get('overall_score', 0),
            'completeness': json_data.get('completeness', 0),
            'accuracy': json_data.get('accuracy', 0),
            'total_activities': summary.get('total_ground_truth_activities', 0),
            'matched_activities': summary.get('total_matched_activities', 0),
            'false_positives': summary.get('false_positives', 0),
            'false_negatives': summary.get('false_negatives', 0),
            'avg_field_score': avg_field_score
        }
    
    else:
        # Drawing parser structure (original)
        return {
            'overall_score': json_data.get('overall_score', 0),
            'room_detection_score': json_data.get('room_detection_score', 0),
            'adjacency_precision': json_data.get('adjacency_precision', 0),
            'adjacency_recall': json_data.get('adjacency_recall', 0),
            'adjacency_f1': json_data.get('adjacency_f1_score', 0),
            'total_rooms': json_data.get('summary', {}).get('total_rooms_ground_truth', 0),
            'key_issues': json_data.get('key_issues', [])
        }

def get_score_color(score):
    """Return color based on score"""
    if score >= 9:
        return '#10b981'  # green
    elif score >= 7:
        return '#f59e0b'  # yellow
    else:
        return '#ef4444'  # red

def create_comparison_table(files_data, parser_type):
    """Create comparison DataFrame based on parser type"""
    if not files_data:
        return None
    
    rows = []
    for file_name, json_data in files_data:
        stats = calculate_stats(json_data, parser_type)
        
        if parser_type == 'financial':
            rows.append({
                'File': file_name,
                'Overall Score': stats['overall_score'],
                'Completeness': stats['completeness'],
                'Accuracy': stats['accuracy'],
                'Avg Item Score': stats['avg_item_score'],
                'Total Sections': stats['total_sections'],
                'Total Items': stats['total_items'],
                'Confidence': stats['confidence']
            })
        elif parser_type == 'gantt':
            rows.append({
                'File': file_name,
                'Overall Score': stats['overall_score'],
                'Completeness': stats['completeness'],
                'Accuracy': stats['accuracy'],
                'Avg Field Score': stats['avg_field_score'],
                'Total Activities': stats['total_activities'],
                'Matched': stats['matched_activities'],
                'False Positives': stats['false_positives'],
                'False Negatives': stats['false_negatives']
            })
        else:
            rows.append({
                'File': file_name,
                'Overall Score': stats['overall_score'],
                'Room Detection': stats['room_detection_score'],
                'Adjacency F1': stats['adjacency_f1'],
                'Precision': stats['adjacency_precision'],
                'Recall': stats['adjacency_recall'],
                'Total Rooms': stats['total_rooms'],
                'Issues Count': len(stats['key_issues'])
            })
    
    return pd.DataFrame(rows)

def display_aggregate_stats(files_data, parser_type):
    """Display aggregate statistics based on parser type"""
    if not files_data:
        return
    
    all_stats = [calculate_stats(data, parser_type) for _, data in files_data]
    
    if parser_type == 'financial':
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_overall = sum(s['overall_score'] for s in all_stats) / len(all_stats)
            st.metric("Avg Overall Score", f"{avg_overall:.2f}")
        
        with col2:
            avg_completeness = sum(s['completeness'] for s in all_stats) / len(all_stats)
            st.metric("Avg Completeness", f"{avg_completeness:.2f}")
        
        with col3:
            avg_accuracy = sum(s['accuracy'] for s in all_stats) / len(all_stats)
            st.metric("Avg Accuracy", f"{avg_accuracy:.2f}")
        
        with col4:
            total_items = sum(s['total_items'] for s in all_stats)
            st.metric("Total Items", total_items)
    
    elif parser_type == 'gantt':
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_overall = sum(s['overall_score'] for s in all_stats) / len(all_stats)
            st.metric("Avg Overall Score", f"{avg_overall:.2f}")
        
        with col2:
            avg_completeness = sum(s['completeness'] for s in all_stats) / len(all_stats)
            st.metric("Avg Completeness", f"{avg_completeness:.2f}")
        
        with col3:
            total_activities = sum(s['total_activities'] for s in all_stats)
            st.metric("Total Activities", total_activities)
        
        with col4:
            total_fps = sum(s['false_positives'] for s in all_stats)
            total_fns = sum(s['false_negatives'] for s in all_stats)
            st.metric("Total FP + FN", total_fps + total_fns)
    
    else:
        # Drawing parsers
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_overall = sum(s['overall_score'] for s in all_stats) / len(all_stats)
            st.metric("Avg Overall Score", f"{avg_overall:.2f}")
        
        with col2:
            avg_room = sum(s['room_detection_score'] for s in all_stats) / len(all_stats)
            st.metric("Avg Room Detection", f"{avg_room:.2f}")
        
        with col3:
            avg_f1 = sum(s['adjacency_f1'] for s in all_stats) / len(all_stats)
            st.metric("Avg Adjacency F1", f"{avg_f1:.2f}")
        
        with col4:
            total_issues = sum(len(s['key_issues']) for s in all_stats)
            st.metric("Total Issues", total_issues)

def create_score_chart(files_data, parser_type):
    """Create bar chart comparing scores based on parser type"""
    if not files_data:
        return None
    
    data = []
    for file_name, json_data in files_data:
        stats = calculate_stats(json_data, parser_type)
        short_name = file_name[:20] + '...' if len(file_name) > 20 else file_name
        
        if parser_type == 'financial':
            data.append({
                'File': short_name,
                'Overall Score': stats['overall_score'],
                'Completeness': stats['completeness'],
                'Accuracy': stats['accuracy']
            })
        elif parser_type == 'gantt':
            data.append({
                'File': short_name,
                'Overall Score': stats['overall_score'],
                'Completeness': stats['completeness'],
                'Accuracy': stats['accuracy']
            })
        else:
            data.append({
                'File': short_name,
                'Overall Score': stats['overall_score'],
                'Room Detection': stats['room_detection_score'],
                'Adjacency F1': stats['adjacency_f1']
            })
    
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    
    if parser_type in ['financial', 'gantt']:
        fig.add_trace(go.Bar(
            name='Overall Score',
            x=df['File'],
            y=df['Overall Score'],
            marker_color='#3b82f6'
        ))
        
        fig.add_trace(go.Bar(
            name='Completeness',
            x=df['File'],
            y=df['Completeness'],
            marker_color='#10b981'
        ))
        
        fig.add_trace(go.Bar(
            name='Accuracy',
            x=df['File'],
            y=df['Accuracy'],
            marker_color='#f59e0b'
        ))
    else:
        fig.add_trace(go.Bar(
            name='Overall Score',
            x=df['File'],
            y=df['Overall Score'],
            marker_color='#3b82f6'
        ))
        
        fig.add_trace(go.Bar(
            name='Room Detection',
            x=df['File'],
            y=df['Room Detection'],
            marker_color='#10b981'
        ))
        
        fig.add_trace(go.Bar(
            name='Adjacency F1',
            x=df['File'],
            y=df['Adjacency F1'],
            marker_color='#f59e0b'
        ))
    
    fig.update_layout(
        barmode='group',
        title='Score Comparison',
        yaxis_title='Score',
        xaxis_title='File',
        height=400
    )
    
    return fig

def create_financial_field_comparison(files_data):
    """Create comparison table for financial parser field scores across all files"""
    if not files_data:
        return None
    
    rows = []
    for file_name, json_data in files_data:
        section_analysis = json_data.get('section_analysis', [])
        
        # Calculate field scores for this file
        field_scores = {
            'item_number': [],
            'item_description': [],
            'unit': [],
            'quantity': [],
            'rate': [],
            'amount': [],
            'currency': []
        }
        
        for section in section_analysis:
            for item in section.get('item_analysis', []):
                match_scores = item.get('match_scores', {})
                for field, score in match_scores.items():
                    if field in field_scores:
                        field_scores[field].append(score)
        
        # Calculate averages and convert to 0-10 scale
        row = {
            'File': file_name,
            'Item Number': (sum(field_scores['item_number']) / len(field_scores['item_number']) * 10) if field_scores['item_number'] else 0,
            'Item Description': (sum(field_scores['item_description']) / len(field_scores['item_description']) * 10) if field_scores['item_description'] else 0,
            'Unit': (sum(field_scores['unit']) / len(field_scores['unit']) * 10) if field_scores['unit'] else 0,
            'Quantity': (sum(field_scores['quantity']) / len(field_scores['quantity']) * 10) if field_scores['quantity'] else 0,
            'Rate': (sum(field_scores['rate']) / len(field_scores['rate']) * 10) if field_scores['rate'] else 0,
            'Amount': (sum(field_scores['amount']) / len(field_scores['amount']) * 10) if field_scores['amount'] else 0,
            'Currency': (sum(field_scores['currency']) / len(field_scores['currency']) * 10) if field_scores['currency'] else 0,
            'Overall Avg': json_data.get('overall_score', 0)
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Add average row at the bottom
    avg_row = {'File': 'AVERAGE'}
    for col in df.columns:
        if col != 'File':
            avg_row[col] = df[col].mean()
    
    df = pd.concat([df, pd.DataFrame([avg_row])], ignore_index=True)
    
    return df

def create_financial_field_chart(files_data):
    """Create grouped bar chart comparing field scores across files"""
    if not files_data:
        return None
    
    chart_data = []
    for file_name, json_data in files_data:
        section_analysis = json_data.get('section_analysis', [])
        
        # Calculate field scores
        field_scores = {
            'item_number': [],
            'item_description': [],
            'unit': [],
            'quantity': [],
            'rate': [],
            'amount': [],
            'currency': []
        }
        
        for section in section_analysis:
            for item in section.get('item_analysis', []):
                match_scores = item.get('match_scores', {})
                for field, score in match_scores.items():
                    if field in field_scores:
                        field_scores[field].append(score)
        
        # Short file name for chart
        short_name = file_name[:15] + '...' if len(file_name) > 15 else file_name
        
        # Add data for each field
        for field_key, field_label in [
            ('item_number', 'Item Number'),
            ('item_description', 'Description'),
            ('unit', 'Unit'),
            ('quantity', 'Quantity'),
            ('rate', 'Rate'),
            ('amount', 'Amount'),
            ('currency', 'Currency')
        ]:
            avg_score = (sum(field_scores[field_key]) / len(field_scores[field_key]) * 10) if field_scores[field_key] else 0
            chart_data.append({
                'File': short_name,
                'Field': field_label,
                'Score': avg_score
            })
    
    df = pd.DataFrame(chart_data)
    
    fig = px.bar(df, x='File', y='Score', color='Field', barmode='group',
                 title='Field Performance Comparison Across Files',
                 height=500)
    fig.update_layout(xaxis_title='File', yaxis_title='Score (0-10)')
    
    return fig

def display_detailed_analysis(file_name, json_data, parser_type):

    """Display detailed analysis based on parser type"""
    
    if parser_type == 'financial':
        st.subheader(f"Financial Analysis - {file_name}")
        
        section_analysis = json_data.get('section_analysis', [])
        
        # Calculate overall field scores across all items
        field_scores = {
            'item_number': [],
            'item_description': [],
            'unit': [],
            'quantity': [],
            'rate': [],
            'amount': [],
            'currency': []
        }
        
        for section in section_analysis:
            for item in section.get('item_analysis', []):
                match_scores = item.get('match_scores', {})
                for field, score in match_scores.items():
                    if field in field_scores:
                        field_scores[field].append(score)
        
        # Display overall field scores
        st.markdown("### 📊 Overall Field Scores")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_item_num = (sum(field_scores['item_number']) / len(field_scores['item_number']) * 10) if field_scores['item_number'] else 0
            st.metric("Item Number", f"{avg_item_num:.2f}")
            
        with col2:
            avg_desc = (sum(field_scores['item_description']) / len(field_scores['item_description']) * 10) if field_scores['item_description'] else 0
            st.metric("Item Description", f"{avg_desc:.2f}")
        
        with col3:
            avg_unit = (sum(field_scores['unit']) / len(field_scores['unit']) * 10) if field_scores['unit'] else 0
            st.metric("Unit", f"{avg_unit:.2f}")
        
        with col4:
            avg_qty = (sum(field_scores['quantity']) / len(field_scores['quantity']) * 10) if field_scores['quantity'] else 0
            st.metric("Quantity", f"{avg_qty:.2f}")
        
        col5, col6, col7 = st.columns(3)
        
        with col5:
            avg_rate = (sum(field_scores['rate']) / len(field_scores['rate']) * 10) if field_scores['rate'] else 0
            st.metric("Rate", f"{avg_rate:.2f}")
        
        with col6:
            avg_amount = (sum(field_scores['amount']) / len(field_scores['amount']) * 10) if field_scores['amount'] else 0
            st.metric("Amount", f"{avg_amount:.2f}")
        
        with col7:
            avg_currency = (sum(field_scores['currency']) / len(field_scores['currency']) * 10) if field_scores['currency'] else 0
            st.metric("Currency", f"{avg_currency:.2f}")
        
        # Create a bar chart for field scores
        field_data = {
            'Field': ['Item Number', 'Description', 'Unit', 'Quantity', 'Rate', 'Amount', 'Currency'],
            'Score': [avg_item_num, avg_desc, avg_unit, avg_qty, avg_rate, avg_amount, avg_currency]
        }
        df_fields = pd.DataFrame(field_data)
        
        fig = px.bar(df_fields, x='Field', y='Score', 
                     title='Field Accuracy Scores',
                     color='Score',
                     color_continuous_scale=['#ef4444', '#f59e0b', '#10b981'],
                     range_color=[0, 10])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Section-by-section breakdown
        for section in section_analysis:
            section_title = section.get('section_title', 'Unknown Section')
            with st.expander(f"📋 {section_title}"):
                items = section.get('item_analysis', [])
                
                # Create a summary table for this section
                item_data = []
                for item in items:
                    match_scores = item.get('match_scores', {})
                    avg_score = sum(match_scores.values()) / len(match_scores) if match_scores else 0
                    
                    item_data.append({
                        'Internal #': item.get('internal_number', 'N/A'),
                        'Avg Score': f"{avg_score:.2f}",
                        'Item Number': match_scores.get('item_number', 0),
                        'Description': match_scores.get('item_description', 0),
                        'Unit': match_scores.get('unit', 0),
                        'Quantity': match_scores.get('quantity', 0),
                        'Rate': match_scores.get('rate', 0),
                        'Amount': match_scores.get('amount', 0),
                        'Currency': match_scores.get('currency', 0)
                    })
                
                if item_data:
                    df = pd.DataFrame(item_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Show items with issues (score < 1.0)
                    issues = [item for item in items 
                             if any(score < 1.0 for score in item.get('match_scores', {}).values())]
                    
                    if issues:
                        st.markdown("**⚠️ Items with Issues:**")
                        for item in issues:
                            notes = item.get('notes', {})
                            st.markdown(f"- **Item {item.get('internal_number')}**: {', '.join([f'{k}: {v}' for k, v in notes.items() if 'Exact' not in v])}")
    
    elif parser_type == 'gantt':
        st.subheader(f"Gantt Analysis - {file_name}")
        
        field_evaluations = json_data.get('field_evaluations', [])
        
        # Create summary table
        eval_data = []
        for evaluation in field_evaluations:
            field_scores = evaluation.get('field_scores', {})
            avg_score = sum(field_scores.values()) / len(field_scores) if field_scores else 0
            
            eval_data.append({
                'Ground Truth ID': evaluation.get('ground_truth_id', 'N/A'),
                'Parser ID': evaluation.get('parser_id', 'N/A'),
                'Avg Score': f"{avg_score:.2f}",
                'ID Match': field_scores.get('id', 0),
                'Task Match': field_scores.get('task', 0),
                'Start Match': field_scores.get('start', 0),
                'Finish Match': field_scores.get('finish', 0),
                'Duration Match': field_scores.get('duration', 0),
                'Notes': evaluation.get('notes', '')
            })
        
        if eval_data:
            df = pd.DataFrame(eval_data)
            
            # Highlight rows with issues
            def highlight_issues(val):
                if isinstance(val, str) and val != '1.00':
                    try:
                        if float(val) < 1.0:
                            return 'background-color: #fee2e2'
                    except:
                        pass
                return ''
            
            styled_df = df.style.applymap(highlight_issues)
            st.dataframe(styled_df, use_container_width=True)
            
            # Show activities with issues
            issues = [e for e in field_evaluations 
                     if any(score < 1.0 for score in e.get('field_scores', {}).values())]
            
            if issues:
                st.markdown("**⚠️ Activities with Mismatches:**")
                for evaluation in issues:
                    gt_id = evaluation.get('ground_truth_id')
                    field_scores = evaluation.get('field_scores', {})
                    mismatches = [k for k, v in field_scores.items() if v < 1.0]
                    st.markdown(f"- **Activity {gt_id}**: Issues in {', '.join(mismatches)}")
                    if evaluation.get('notes'):
                        st.markdown(f"  *Note: {evaluation.get('notes')}*")
    
    else:
        # Drawing parser - use existing room analysis
        display_room_analysis(file_name, json_data)

def display_comparison_view(ai_files_data, det_files_data):
    """Display AI vs Deterministic comparison for neighboring rooms"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("AI Method")
        if ai_files_data:
            ai_comparison = []
            for file_name, json_data in ai_files_data:
                stats = calculate_stats(json_data, 'drawing')
                ai_comparison.append({
                    'File': file_name,
                    'Overall Score': stats['overall_score'],
                    'Room Detection': stats['room_detection_score'],
                    'Adjacency F1': stats['adjacency_f1'],
                    'Precision': stats['adjacency_precision'],
                    'Recall': stats['adjacency_recall']
                })
            df_ai = pd.DataFrame(ai_comparison)
            
            def highlight_scores(val):
                if isinstance(val, (int, float)):
                    if val >= 9:
                        return 'background-color: #d1fae5'
                    elif val >= 7:
                        return 'background-color: #fef3c7'
                    elif val < 7 and val > 0:
                        return 'background-color: #fee2e2'
                return ''
            
            styled_df = df_ai.style.applymap(
                highlight_scores,
                subset=['Overall Score', 'Room Detection', 'Adjacency F1']
            )
            st.dataframe(styled_df, use_container_width=True)
            
            # Calculate averages
            st.markdown("**Averages:**")
            avg_col1, avg_col2, avg_col3 = st.columns(3)
            with avg_col1:
                st.metric("Avg Overall", f"{df_ai['Overall Score'].mean():.2f}")
            with avg_col2:
                st.metric("Avg Room Det.", f"{df_ai['Room Detection'].mean():.2f}")
            with avg_col3:
                st.metric("Avg Adj F1", f"{df_ai['Adjacency F1'].mean():.2f}")
        else:
            st.info("No AI method data available. Upload files in the 'Drawing - Neighboring (AI)' tab.")
    
    with col2:
        st.subheader("Deterministic Method")
        if det_files_data:
            det_comparison = []
            for file_name, json_data in det_files_data:
                stats = calculate_stats(json_data, 'drawing')
                det_comparison.append({
                    'File': file_name,
                    'Overall Score': stats['overall_score'],
                    'Room Detection': stats['room_detection_score'],
                    'Adjacency F1': stats['adjacency_f1'],
                    'Precision': stats['adjacency_precision'],
                    'Recall': stats['adjacency_recall']
                })
            df_det = pd.DataFrame(det_comparison)
            
            def highlight_scores(val):
                if isinstance(val, (int, float)):
                    if val >= 9:
                        return 'background-color: #d1fae5'
                    elif val >= 7:
                        return 'background-color: #fef3c7'
                    elif val < 7 and val > 0:
                        return 'background-color: #fee2e2'
                return ''
            
            styled_df = df_det.style.applymap(
                highlight_scores,
                subset=['Overall Score', 'Room Detection', 'Adjacency F1']
            )
            st.dataframe(styled_df, use_container_width=True)
            
            # Calculate averages
            st.markdown("**Averages:**")
            avg_col1, avg_col2, avg_col3 = st.columns(3)
            with avg_col1:
                st.metric("Avg Overall", f"{df_det['Overall Score'].mean():.2f}")
            with avg_col2:
                st.metric("Avg Room Det.", f"{df_det['Room Detection'].mean():.2f}")
            with avg_col3:
                st.metric("Avg Adj F1", f"{df_det['Adjacency F1'].mean():.2f}")
        else:
            st.info("No Deterministic method data available. Upload files in the 'Drawing - Neighboring (Deterministic)' tab.")

# Main App
st.title("📊 Validation JSON Comparison Dashboard")
st.markdown("Upload and compare validation results across different parsers")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Financial Parser",
    "Gantt Parser", 
    "Drawing - Titleblock",
    "Drawing - Neighboring (AI)",
    "Drawing - Neighboring (Deterministic)",
    "Drawing - Full Plan AI"
])

tabs_config = [
    (tab1, 'financial', 'Financial Parser', 'financial'),
    (tab2, 'gantt', 'Gantt Parser', 'gantt'),
    (tab3, 'drawing_titleblock', 'Drawing - Titleblock', 'drawing'),
    (tab4, 'drawing_neighboring_ai', 'Drawing - Neighboring (AI)', 'drawing'),
    (tab5, 'drawing_neighboring_deterministic', 'Drawing - Neighboring (Deterministic)', 'drawing'),
    (tab6, 'drawing_fullplan_ai', 'Drawing - Full Plan AI', 'drawing')
]

for tab, key, label, parser_type in tabs_config:
    with tab:
        st.header(label)
        
        # File uploader
        uploaded_files = st.file_uploader(
            f"Upload JSON files for {label}",
            type=['json'],
            accept_multiple_files=True,
            key=f"uploader_{key}"
        )
        
        if uploaded_files:
            files_data = []
            for uploaded_file in uploaded_files:
                json_data = load_json_file(uploaded_file)
                if json_data:
                    files_data.append((uploaded_file.name, json_data))
            
            # Store in session state for cross-tab comparison
            st.session_state.files[key] = files_data
            
            if files_data:
                # Aggregate statistics
                st.subheader("📈 Aggregate Statistics")
                display_aggregate_stats(files_data, parser_type)
                
                st.divider()
                
                # Score chart
                st.subheader("📊 Score Comparison Chart")
                chart = create_score_chart(files_data, parser_type)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                
                st.divider()
                
                # Comparison table
                st.subheader("📋 Comparison Table")
                df = create_comparison_table(files_data, parser_type)
                if df is not None:
                    # Style the dataframe
                    def highlight_scores(val):
                        if isinstance(val, (int, float)):
                            if val >= 9:
                                return 'background-color: #d1fae5'
                            elif val >= 7:
                                return 'background-color: #fef3c7'
                            elif val < 7 and val > 0:
                                return 'background-color: #fee2e2'
                        return ''
                    
                    if parser_type == 'financial':
                        styled_df = df.style.applymap(
                            highlight_scores,
                            subset=['Overall Score', 'Completeness', 'Accuracy']
                        )
                    elif parser_type == 'gantt':
                        styled_df = df.style.applymap(
                            highlight_scores,
                            subset=['Overall Score', 'Completeness', 'Accuracy']
                        )
                    else:
                        styled_df = df.style.applymap(
                            highlight_scores,
                            subset=['Overall Score', 'Room Detection', 'Adjacency F1']
                        )
                    
                    st.dataframe(styled_df, use_container_width=True)
                
                # Financial field comparison
                if parser_type == 'financial':
                    st.divider()
                    st.subheader("Field-by-Field Performance Comparison")
                    
                    # Field comparison table
                    field_df = create_financial_field_comparison(files_data)
                    if field_df is not None:
                        st.markdown("**Performance by Field Across All Files:**")
                        
                        def highlight_field_scores(val):
                            if isinstance(val, (int, float)):
                                if val >= 9:
                                    return 'background-color: #d1fae5'
                                elif val >= 7:
                                    return 'background-color: #fef3c7'
                                elif val < 7 and val > 0:
                                    return 'background-color: #fee2e2'
                            return ''
                        
                        # Apply styling to all numeric columns
                        numeric_cols = ['Item Number', 'Item Description', 'Unit', 'Quantity', 'Rate', 'Amount', 'Currency', 'Overall Avg']
                        styled_field_df = field_df.style.applymap(
                            highlight_field_scores,
                            subset=numeric_cols
                        ).format({col: '{:.2f}' for col in numeric_cols})
                        
                        st.dataframe(styled_field_df, use_container_width=True)
                    
                    # Field comparison chart
                    field_chart = create_financial_field_chart(files_data)
                    if field_chart:
                        st.plotly_chart(field_chart, use_container_width=True)
                
                st.divider()
                
                # Special comparison for neighboring rooms
                if key in ['drawing_neighboring_ai', 'drawing_neighboring_deterministic']:
                    st.subheader("🔄 AI vs Deterministic Comparison")
                    # Get files from both tabs
                    ai_files = st.session_state.files.get('drawing_neighboring_ai', [])
                    det_files = st.session_state.files.get('drawing_neighboring_deterministic', [])
                    
                    if ai_files or det_files:
                        display_comparison_view(ai_files, det_files)
                    else:
                        st.info("Upload files in both 'AI' and 'Deterministic' tabs to see the comparison.")
                
                st.divider()
                
                # Detailed analysis
                if parser_type in ['financial', 'gantt']:
                    st.subheader("🔍 Detailed Analysis")
                    for file_name, json_data in files_data:
                        with st.expander(f"View details for {file_name}"):
                            display_detailed_analysis(file_name, json_data, parser_type)
                else:
                    # Room analysis for drawing parsers
                    st.subheader("🏠 Detailed Room Analysis")
                    for file_name, json_data in files_data:
                        with st.expander(f"View details for {file_name}"):
                            display_room_analysis(file_name, json_data)
                            
                            # Key issues
                            key_issues = json_data.get('key_issues', [])
                            if key_issues:
                                st.markdown("**⚠️ Key Issues:**")
                                for issue in key_issues:
                                    st.markdown(f"- {issue}")
        else:
            st.info(f"👆 Upload JSON files to start comparing {label} results")

# Sidebar with instructions
with st.sidebar:
    st.header("📖 Instructions")
    st.markdown("""
    1. Navigate to the appropriate tab for your parser type
    2. Upload one or more JSON validation files
    3. View aggregate statistics and comparisons
    4. Explore detailed room analysis
    
    **Color coding:**
    - 🟢 Green: Score ≥ 9
    - 🟡 Yellow: Score ≥ 7
    - 🔴 Red: Score < 7
    """)
    
    st.divider()
    
    st.header("ℹ️ About")
    st.markdown("""
    This dashboard helps you compare validation results across:
    - Financial Parser
    - Gantt Parser
    - Drawing parsers (Titleblock, Neighboring, Full Plan)
    
    For neighboring rooms, you can compare AI vs Deterministic methods.
    """)