import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import io
import base64
from datetime import datetime

st.set_page_config(page_title="Defect Detection Dashboard", layout="wide")

st.title("🏭 Industrial Defect Detection System")
st.markdown("Real-time monitoring & quality control dashboard")

# Initialize session state
if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"
if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_url = st.text_input("API Endpoint", st.session_state.api_url)
    st.session_state.api_url = api_url
    
    st.divider()
    st.header("📊 Quick Stats")
    
    try:
        health_response = requests.get(f"{st.session_state.api_url}/health", timeout=2)
        if health_response.status_code == 200:
            st.success("✅ API Connected")
            # Get system stats
            stats_response = requests.get(f"{st.session_state.api_url}/stats", timeout=2)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                st.metric("Total Processed", stats.get('total_processed', 0))
                st.metric("Defect Rate", f"{stats.get('defect_rate', 0):.1f}%")
                st.metric("Avg Processing Time", f"{stats.get('avg_processing_time', 0):.0f}ms")
    except:
        st.error("❌ API Connection Failed")
    
    st.divider()
    st.header("📁 Sample Images")
    
    # Quick test buttons
    sample_images = {
        "Perfect": "demo_perfect.jpg",
        "Crack": "demo_crack.jpg", 
        "Scratch": "demo_scratch.jpg",
        "Defective": "factory_defective.jpg"
    }
    
    for label, filename in sample_images.items():
        if st.button(f"Test {label}"):
            try:
                with open(filename, 'rb') as f:
                    files = {"file": (filename, f, "image/jpeg")}
                    response = requests.post(f"{st.session_state.api_url}/detect", files=files)
                    if response.status_code == 200:
                        st.session_state.last_result = response.json()
                        st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# Main dashboard tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Live Detection", "📈 Analytics", "📋 History", "⚙️ System Monitor"])

with tab1:
    st.subheader("Real-time Defect Detection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload production image", 
                                        type=['jpg', 'jpeg', 'png', 'bmp'],
                                        help="Upload image of manufactured product")
        
        if uploaded_file is not None:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", width=400)
            
            # Process buttons
            process_col1, process_col2 = st.columns(2)
            with process_col1:
                if st.button("🚀 Analyze for Defects", type="primary", use_container_width=True):
                    with st.spinner("Processing image..."):
                        try:
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                            response = requests.post(f"{st.session_state.api_url}/detect", files=files)
                            
                            if response.status_code == 200:
                                result = response.json()
                                st.session_state.last_result = result
                                st.session_state.history.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'filename': uploaded_file.name,
                                    'result': result
                                })
                                st.success("Analysis complete!")
                            else:
                                st.error(f"API Error: {response.status_code}")
                        except Exception as e:
                            st.error(f"Connection error: {e}")
            
            with process_col2:
                if st.button("🔄 Reset", use_container_width=True):
                    if 'last_result' in st.session_state:
                        del st.session_state.last_result
    
    with col2:
        if 'last_result' in st.session_state:
            result = st.session_state.last_result
            
            # Result metrics
            st.subheader("Detection Results")
            
            # Status card
            if result['defects_found'] > 0:
                st.error(f"❌ **REJECTED** - {result['defects_found']} defects found")
            else:
                st.success("✅ **ACCEPTED** - No defects")
            
            # Metrics
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Defect %", f"{result['defect_percentage']:.2f}%")
            with m2:
                st.metric("Processing Time", f"{result['processing_time_ms']:.0f}ms")
            with m3:
                st.metric("Confidence", f"{result.get('confidence', 95):.0f}%")
            
            # Defect details
            with st.expander("View Defect Details"):
                st.json(result)
            
            # Visualize defects if available
            if 'defect_image' in result:
                try:
                    # Decode base64 image
                    defect_img = base64.b64decode(result['defect_image'])
                    defect_image = Image.open(io.BytesIO(defect_img))
                    st.image(defect_image, caption="Detected Defects", width=300)
                except:
                    pass

with tab2:
    st.subheader("Production Analytics")
    
    # Generate sample analytics (replace with real API data)
    dates = pd.date_range(start='2024-11-01', end='2024-12-04', freq='D')
    defect_rates = [2.1, 1.8, 3.2, 2.5, 1.9, 4.1, 2.8, 3.5, 2.2, 1.7, 2.9, 3.1, 2.4, 1.6, 2.7, 3.8, 2.3, 1.5, 3.9, 2.6, 4.2, 3.3, 2.0, 1.4, 3.4, 2.8, 4.0, 3.6, 2.1, 1.8, 3.7, 2.9, 4.3]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=defect_rates, mode='lines+markers', 
                            name='Defect Rate', line=dict(color='red', width=2)))
    fig.update_layout(title='Defect Rate Trend (Last 30 Days)',
                     xaxis_title='Date',
                     yaxis_title='Defect Rate %',
                     template='plotly_white')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Defect types distribution
    col1, col2 = st.columns(2)
    
    with col1:
        defect_types = {
            'Cracks': 45,
            'Scratches': 30,
            'Discoloration': 15,
            'Misalignment': 10
        }
        
        fig2 = go.Figure(data=[go.Pie(labels=list(defect_types.keys()), 
                                     values=list(defect_types.values()),
                                     hole=.3)])
        fig2.update_layout(title='Defect Type Distribution')
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        # Production stats
        stats_data = {
            'Metric': ['Total Processed', 'Accepted', 'Rejected', 'Avg Processing Time'],
            'Value': [12543, 11916, 627, '187ms']
        }
        df_stats = pd.DataFrame(stats_data)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Processing History")
    
    if st.session_state.history:
        history_data = []
        for entry in reversed(st.session_state.history[-20:]):  # Last 20 entries
            history_data.append({
                'Time': datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                'File': entry['filename'],
                'Defects': entry['result']['defects_found'],
                'Defect %': f"{entry['result']['defect_percentage']:.2f}%",
                'Status': 'REJECTED' if entry['result']['defects_found'] > 0 else 'ACCEPTED',
                'Time (ms)': entry['result']['processing_time_ms']
            })
        
        df_history = pd.DataFrame(history_data)
        st.dataframe(df_history, use_container_width=True)
        
        # Export button
        if st.button("Export History to CSV"):
            csv = df_history.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"defect_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No processing history yet. Upload and analyze images to build history.")

with tab4:
    st.subheader("System Monitoring")
    
    try:
        # Get system health
        health_response = requests.get(f"{st.session_state.api_url}/health", timeout=2)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("API Status", "✅ Healthy" if health_data.get('status') == 'healthy' else "⚠️ Warning")
                st.metric("Uptime", health_data.get('uptime', 'N/A'))
            
            with col2:
                st.metric("Version", health_data.get('version', '1.0.0'))
                st.metric("Model", health_data.get('model_version', 'v1.0'))
            
            with col3:
                # Simulate system metrics
                st.progress(75, text="CPU Usage: 75%")
                st.progress(62, text="Memory Usage: 62%")
                st.progress(15, text="GPU Usage: 15%")
            
            # Kubernetes pods status (simulated)
            st.subheader("Kubernetes Deployment Status")
            pods_data = {
                'Pod': ['ml-api-pod-1', 'ml-api-pod-2', 'redis-cache', 'monitoring-agent'],
                'Status': ['Running', 'Running', 'Running', 'Running'],
                'Ready': ['2/2', '2/2', '1/1', '1/1'],
                'Restarts': [0, 0, 0, 0],
                'Age': ['5d', '5d', '10d', '2d']
            }
            st.dataframe(pd.DataFrame(pods_data), use_container_width=True, hide_index=True)
            
        else:
            st.error("Cannot fetch system health")
    except:
        st.error("API not reachable")

# Footer
st.divider()
st.caption(f"Dashboard v1.0 | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")