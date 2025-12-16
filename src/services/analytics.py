"""
Analytics & Visualization Service
Provides interactive charts, dashboards, and analytics for Pharma AI.
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd


class ChartService:
    """Generate interactive Plotly charts for pharmaceutical data."""
    
    # Color palette
    COLORS = {
        "primary": "#1a365d",
        "secondary": "#2b6cb0",
        "success": "#48bb78",
        "warning": "#ecc94b",
        "danger": "#fc8181",
        "info": "#4299e1",
        "purple": "#805ad5",
        "pink": "#ed64a6",
        "teal": "#38b2ac",
        "orange": "#ed8936"
    }
    
    PALETTE = ["#2b6cb0", "#48bb78", "#ecc94b", "#fc8181", "#805ad5", "#ed64a6", "#38b2ac", "#ed8936"]
    
    @classmethod
    def market_size_chart(cls, data: List[Dict]) -> go.Figure:
        """Create market size comparison bar chart."""
        if not data:
            return cls._empty_chart("No market data available")
        
        df = pd.DataFrame(data)
        
        fig = px.bar(
            df,
            x="molecule",
            y="market_size_usd_mn",
            color="therapy_area",
            title="Market Size by Molecule",
            labels={"market_size_usd_mn": "Market Size (USD Million)", "molecule": "Molecule"},
            color_discrete_sequence=cls.PALETTE,
            template="plotly_white"
        )
        
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    @classmethod
    def cagr_comparison_chart(cls, data: List[Dict]) -> go.Figure:
        """Create CAGR comparison horizontal bar chart."""
        if not data:
            return cls._empty_chart("No CAGR data available")
        
        df = pd.DataFrame(data)
        
        # Handle None/NaN values in cagr_percent
        df["cagr_percent"] = pd.to_numeric(df["cagr_percent"], errors="coerce").fillna(0)
        df = df.sort_values("cagr_percent", ascending=True)
        
        # Color by CAGR value with None handling
        colors = [
            cls.COLORS["danger"] if c < 5 else 
            cls.COLORS["warning"] if c < 10 else 
            cls.COLORS["success"] 
            for c in df["cagr_percent"]
        ]
        
        fig = go.Figure(go.Bar(
            x=df["cagr_percent"],
            y=df["molecule"],
            orientation='h',
            marker_color=colors,
            text=[f"{c:.1f}%" for c in df["cagr_percent"]],
            textposition="outside"
        ))
        
        fig.update_layout(
            title="Growth Rate (CAGR) by Molecule",
            xaxis_title="CAGR (%)",
            yaxis_title="",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            template="plotly_white"
        )
        
        return fig
    
    @classmethod
    def competition_matrix(cls, data: List[Dict]) -> go.Figure:
        """Create competition vs patient burden scatter plot."""
        if not data:
            return cls._empty_chart("No competition data available")
        
        df = pd.DataFrame(data)
        
        # Map competition levels to numeric
        comp_map = {"Low": 1, "Medium": 2, "High": 3}
        burden_map = {"Low": 1, "Medium": 2, "High": 3, "Very High": 4}
        
        df["comp_score"] = df.get("competition_level", df.get("generic_penetration", "Medium")).map(comp_map).fillna(2)
        df["burden_score"] = df.get("patient_burden", "Medium").map(burden_map).fillna(2)
        
        fig = px.scatter(
            df,
            x="comp_score",
            y="burden_score",
            size="market_size_usd_mn",
            color="therapy_area",
            hover_name="molecule",
            title="Whitespace Analysis: Competition vs Patient Burden",
            labels={"comp_score": "Competition Level", "burden_score": "Patient Burden"},
            color_discrete_sequence=cls.PALETTE,
            template="plotly_white"
        )
        
        # Add quadrant lines
        fig.add_hline(y=2.5, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=2, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Add annotations for quadrants
        fig.add_annotation(x=1.5, y=3.5, text="🎯 Sweet Spot", showarrow=False, font=dict(size=12, color="green"))
        fig.add_annotation(x=2.5, y=1.5, text="⚠️ Crowded", showarrow=False, font=dict(size=12, color="red"))
        
        fig.update_layout(
            height=450,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(ticktext=["Low", "Medium", "High"], tickvals=[1, 2, 3]),
            yaxis=dict(ticktext=["Low", "Medium", "High", "Very High"], tickvals=[1, 2, 3, 4])
        )
        
        return fig
    
    @classmethod
    def patent_timeline(cls, data: List[Dict]) -> go.Figure:
        """Create patent expiry timeline."""
        if not data:
            return cls._empty_chart("No patent data available")
        
        events = []
        for item in data:
            mol = item.get("molecule", "Unknown")
            # Handle both nested patents and flat patent records
            patents_list = item.get("patents", [item])
            for patent in patents_list:
                expiry = patent.get("expiry_date")
                if expiry:
                    # Get status - handle enum values
                    status = patent.get("status", "Active")
                    if hasattr(status, 'value'):
                        status = status.value
                    status = str(status)
                    
                    events.append({
                        "molecule": mol,
                        "patent": patent.get("patent_number", "N/A"),
                        "type": patent.get("type", patent.get("patent_type", "Unknown")),
                        "expiry": expiry if isinstance(expiry, str) else expiry.strftime("%Y-%m-%d"),
                        "status": status
                    })
        
        if not events:
            return cls._empty_chart("No patent expiry data")
        
        df = pd.DataFrame(events)
        df["expiry_date"] = pd.to_datetime(df["expiry"])
        df = df.sort_values("expiry_date")
        
        # Color by status - handle various status formats
        color_map = {
            "Active": cls.COLORS["success"], 
            "Expired": cls.COLORS["danger"], 
            "Pending": cls.COLORS["warning"],
            "ACTIVE": cls.COLORS["success"],
            "EXPIRED": cls.COLORS["danger"],
            "PENDING": cls.COLORS["warning"]
        }
        df["color"] = df["status"].map(color_map).fillna(cls.COLORS["info"])
        
        fig = go.Figure()
        
        for idx, row in df.iterrows():
            fig.add_trace(go.Scatter(
                x=[row["expiry_date"]],
                y=[row["molecule"]],
                mode="markers+text",
                marker=dict(size=20, color=row["color"], symbol="diamond"),
                text=row["patent"],
                textposition="top center",
                name=row["status"],
                hovertemplate=f"<b>{row['molecule']}</b><br>Patent: {row['patent']}<br>Type: {row['type']}<br>Expiry: {row['expiry']}<extra></extra>"
            ))
        
        fig.update_layout(
            title="Patent Expiry Timeline",
            xaxis_title="Expiry Date",
            yaxis_title="",
            height=400,
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=20),
            template="plotly_white"
        )
        
        # Add today line - use shape instead of vline to avoid annotation issues
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")
        
        fig.add_shape(
            type="line",
            x0=today_str, x1=today_str,
            y0=0, y1=1,
            yref="paper",
            line=dict(color="red", dash="dash", width=2)
        )
        
        # Add annotation separately
        fig.add_annotation(
            x=today_str,
            y=1,
            yref="paper",
            text="Today",
            showarrow=False,
            font=dict(color="red"),
            yshift=10
        )
        
        return fig
    
    @classmethod
    def clinical_trials_funnel(cls, data: List[Dict]) -> go.Figure:
        """Create clinical trial phase funnel."""
        if not data:
            return cls._empty_chart("No clinical trial data available")
        
        # Count trials by phase
        phase_counts = {"Phase I": 0, "Phase II": 0, "Phase III": 0, "Phase IV": 0}
        
        for item in data:
            for trial in item.get("active_trials", [item]):
                phase = trial.get("phase", "")
                for key in phase_counts:
                    if key in phase:
                        phase_counts[key] += 1
                        break
        
        phases = list(phase_counts.keys())
        counts = list(phase_counts.values())
        
        fig = go.Figure(go.Funnel(
            y=phases,
            x=counts,
            textinfo="value+percent initial",
            marker=dict(color=[cls.COLORS["info"], cls.COLORS["secondary"], cls.COLORS["success"], cls.COLORS["purple"]])
        ))
        
        fig.update_layout(
            title="Clinical Trial Pipeline by Phase",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            template="plotly_white"
        )
        
        return fig
    
    @classmethod
    def sentiment_gauge(cls, sentiment: float, molecule: str = "") -> go.Figure:
        """Create sentiment gauge chart."""
        # Normalize sentiment from [-1, 1] to [0, 100]
        value = (sentiment + 1) * 50
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain=dict(x=[0, 1], y=[0, 1]),
            title=dict(text=f"Patient Sentiment{' - ' + molecule if molecule else ''}"),
            delta=dict(reference=50),
            gauge=dict(
                axis=dict(range=[0, 100], tickwidth=1),
                bar=dict(color=cls.COLORS["primary"]),
                steps=[
                    dict(range=[0, 33], color=cls.COLORS["danger"]),
                    dict(range=[33, 66], color=cls.COLORS["warning"]),
                    dict(range=[66, 100], color=cls.COLORS["success"])
                ],
                threshold=dict(
                    line=dict(color="black", width=4),
                    thickness=0.75,
                    value=value
                )
            )
        ))
        
        fig.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    @classmethod
    def therapy_area_pie(cls, data: List[Dict]) -> go.Figure:
        """Create therapy area distribution pie chart."""
        if not data:
            return cls._empty_chart("No therapy area data")
        
        df = pd.DataFrame(data)
        therapy_counts = df["therapy_area"].value_counts()
        
        fig = px.pie(
            values=therapy_counts.values,
            names=therapy_counts.index,
            title="Market Distribution by Therapy Area",
            color_discrete_sequence=cls.PALETTE,
            hole=0.4
        )
        
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    @classmethod
    def api_usage_chart(cls, usage_data: Dict) -> go.Figure:
        """Create API usage progress bars."""
        apis = list(usage_data.keys())
        used = [usage_data[api].get("global_calls", 0) for api in apis]
        limits = [usage_data[api].get("global_limit", 100) for api in apis]
        remaining = [l - u for u, l in zip(used, limits)]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name="Used",
            y=apis,
            x=used,
            orientation='h',
            marker_color=cls.COLORS["primary"]
        ))
        
        fig.add_trace(go.Bar(
            name="Remaining",
            y=apis,
            x=remaining,
            orientation='h',
            marker_color=cls.COLORS["success"],
            opacity=0.5
        ))
        
        fig.update_layout(
            title="API Usage Today",
            barmode='stack',
            height=200,
            margin=dict(l=20, r=20, t=40, b=20),
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        
        return fig
    
    @classmethod
    def molecule_comparison(cls, molecules: List[str], data: List[Dict]) -> go.Figure:
        """Create molecule comparison radar chart."""
        if not data or not molecules:
            return cls._empty_chart("No comparison data")
        
        # Filter data for selected molecules
        df = pd.DataFrame(data)
        df = df[df["molecule"].isin(molecules)]
        
        if df.empty:
            return cls._empty_chart("Selected molecules not found")
        
        # Prepare radar chart data
        categories = ["Market Size", "CAGR", "Competition", "Patient Burden"]
        
        fig = go.Figure()
        
        for _, row in df.iterrows():
            # Normalize values to 0-100 scale
            market_norm = min(100, row.get("market_size_usd_mn", 0) / 250 * 100)
            cagr_norm = min(100, row.get("cagr_percent", 0) * 5)
            
            comp_map = {"Low": 80, "Medium": 50, "High": 20}
            comp_norm = comp_map.get(row.get("competition_level", row.get("generic_penetration", "Medium")), 50)
            
            burden_map = {"Low": 25, "Medium": 50, "High": 75, "Very High": 100}
            burden_norm = burden_map.get(row.get("patient_burden", "Medium"), 50)
            
            values = [market_norm, cagr_norm, comp_norm, burden_norm]
            
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],  # Close the polygon
                theta=categories + [categories[0]],
                fill='toself',
                name=row["molecule"],
                opacity=0.6
            ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title="Molecule Comparison",
            height=400,
            margin=dict(l=60, r=60, t=60, b=60)
        )
        
        return fig
    
    @classmethod
    def _empty_chart(cls, message: str) -> go.Figure:
        """Create empty chart with message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            height=300,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            template="plotly_white"
        )
        return fig


class AnalyticsService:
    """Track and analyze query patterns and usage."""
    
    @classmethod
    def log_query(cls, query: str, agents_used: List[str], response_time_ms: float, user_id: Optional[int] = None):
        """Log a query for analytics (delegates to QueryTracker)."""
        try:
            from src.services.query_tracker import QueryTracker
            QueryTracker.log_query(
                query_text=query,
                agents_used=agents_used,
                user_id=user_id,
                response_time_ms=int(response_time_ms)
            )
        except Exception:
            pass  # Fallback silently
    
    @classmethod
    def get_popular_queries(cls, limit: int = 10) -> List[Dict]:
        """Get most common query patterns."""
        try:
            from src.services.query_tracker import QueryTracker
            keywords = QueryTracker.get_popular_queries(limit)
            return [{"term": k["keyword"], "count": k["count"]} for k in keywords]
        except Exception:
            return []
    
    @classmethod
    def get_agent_usage(cls) -> Dict[str, int]:
        """Get agent usage statistics."""
        try:
            from src.services.query_tracker import QueryTracker
            return QueryTracker.get_agent_distribution()
        except Exception:
            return {}
    
    @classmethod
    def get_avg_response_time(cls) -> float:
        """Get average response time in milliseconds."""
        try:
            from src.services.query_tracker import QueryTracker
            return QueryTracker.get_avg_response_time()
        except Exception:
            return 0.0
    
    @classmethod
    def get_queries_today(cls) -> int:
        """Get number of queries today."""
        try:
            from src.services.query_tracker import QueryTracker
            return QueryTracker.get_total_queries(1)
        except Exception:
            return 0
    
    @classmethod
    def get_dashboard_stats(cls) -> Dict:
        """Get all dashboard statistics."""
        try:
            from src.services.query_tracker import QueryTracker
            return {
                "total_queries": QueryTracker.get_total_queries(365),
                "queries_today": QueryTracker.get_total_queries(1),
                "avg_response_time": round(QueryTracker.get_avg_response_time(), 2),
                "agent_usage": QueryTracker.get_agent_distribution(),
                "popular_terms": cls.get_popular_queries(5),
                "success_rate": QueryTracker.get_success_rate()
            }
        except Exception:
            return {
                "total_queries": 0,
                "queries_today": 0,
                "avg_response_time": 0,
                "agent_usage": {},
                "popular_terms": [],
                "success_rate": 100.0
            }
