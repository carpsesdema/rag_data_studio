# rag_data_studio/components/browser.py
"""
The interactive QWebEngineView component for visual element selection.
"""
import uuid
import json
from PySide6.QtCore import Signal, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView

class InteractiveBrowser(QWebEngineView):
    element_selected = Signal(str, str, str)

    def __init__(self):
        super().__init__()
        self.targeting_active = False
        self.page().profile().setHttpUserAgent("DataExtractorStudio/1.0 InteractiveBrowser")
        self.TARGETING_JS_OVERLAY_ID = f"__dataExtractorOverlay_{uuid.uuid4().hex}"
        self.TARGETING_JS_TOOLTIP_ID = f"__dataExtractorTooltip_{uuid.uuid4().hex}"
        self.TARGETING_JS_SELECTION_VAR = f"__dataExtractorSelection_{uuid.uuid4().hex}"

    def _get_targeting_js(self):
        return f"""
        (function() {{
            if (window.{self.TARGETING_JS_SELECTION_VAR}_active) return;
            window.{self.TARGETING_JS_SELECTION_VAR}_active = true;
            console.log('ExtractorStudio: Targeting mode activated.');
            const overlayId = '{self.TARGETING_JS_OVERLAY_ID}';
            const tooltipId = '{self.TARGETING_JS_TOOLTIP_ID}';
            const selectionVar = '{self.TARGETING_JS_SELECTION_VAR}';
            let currentTarget = null;
            document.getElementById(overlayId)?.remove();
            document.getElementById(tooltipId)?.remove();
            const overlay = document.createElement('div');
            overlay.id = overlayId;
            overlay.style.cssText = `position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(76, 175, 80, 0.05); z-index: 2147483640; pointer-events: none; border: 2px dashed #4CAF50; box-sizing: border-box;`;
            document.body.appendChild(overlay);
            const tooltip = document.createElement('div');
            tooltip.id = tooltipId;
            tooltip.style.cssText = `position: fixed; top: 10px; right: 10px; background: #4CAF50; color: white; padding: 8px 12px; border-radius: 5px; z-index: 2147483641; font-family: Arial, sans-serif; font-size: 13px; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.2);`;
            tooltip.textContent = '🎯 Click an element to select';
            document.body.appendChild(tooltip);
            function generateSelector(el) {{
                if (!(el instanceof Element)) return;
                const parts = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {{
                    let selector = el.nodeName.toLowerCase();
                    if (el.id) {{
                        selector += '#' + el.id.trim().replace(/\\s+/g, '-');
                        parts.unshift(selector); break;
                    }} else {{
                        let cls = Array.from(el.classList).filter(c => c.trim() !== '').slice(0,2).join('.');
                        if (cls) selector += '.' + cls;
                        let sib = el, nth = 1;
                        while (sib = sib.previousElementSibling) {{
                            if (sib.nodeName.toLowerCase() == selector.split('.')[0]) nth++;
                        }}
                        if (nth != 1) selector += `:nth-of-type(${{nth}})`;
                    }}
                    parts.unshift(selector); el = el.parentNode;
                }}
                return parts.join(' > ');
            }}
            function mouseMoveHandler(event) {{
                if (!window.{self.TARGETING_JS_SELECTION_VAR}_active) return;
                const el = event.target;
                if (el === currentTarget || el === overlay || el === tooltip) return;
                currentTarget = el;
                if (currentTarget) {{
                    currentTarget.style.outline = '2px solid #FF5722';
                    currentTarget.style.backgroundColor = 'rgba(255, 87, 34, 0.1)';
                    const rect = currentTarget.getBoundingClientRect();
                    overlay.style.width = rect.width + 'px'; overlay.style.height = rect.height + 'px';
                    overlay.style.top = rect.top + 'px'; overlay.style.left = rect.left + 'px';
                    overlay.style.display = 'block';
                }}
            }}
            function mouseOutHandler(event) {{
                if (!window.{self.TARGETING_JS_SELECTION_VAR}_active) return;
                if (event.target === currentTarget && currentTarget) {{
                    currentTarget.style.outline = ''; currentTarget.style.backgroundColor = '';
                    overlay.style.display = 'none'; currentTarget = null;
                }}
            }}
            function clickHandler(event) {{
                if (!window.{self.TARGETING_JS_SELECTION_VAR}_active) return;
                event.preventDefault(); event.stopPropagation();
                const el = event.target;
                const selector = generateSelector(el);
                const text = el.textContent ? el.textContent.trim().substring(0, 500) : '';
                const elementType = el.tagName.toLowerCase();
                window[selectionVar] = {{ selector, text, type: elementType }};
                console.log('ExtractorStudio: Element selected:', window[selectionVar]);
                disableTargetingModeInternal();
            }}
            function disableTargetingModeInternal() {{
                console.log('ExtractorStudio: Disabling targeting mode internally.');
                document.removeEventListener('mousemove', mouseMoveHandler, true);
                document.removeEventListener('mouseout', mouseOutHandler, true);
                document.removeEventListener('click', clickHandler, true);
                if (currentTarget) {{ currentTarget.style.outline = ''; currentTarget.style.backgroundColor = ''; }}
                overlay.remove(); tooltip.remove();
                window.{self.TARGETING_JS_SELECTION_VAR}_active = false;
            }}
            window['__cleanup_' + selectionVar] = disableTargetingModeInternal;
            document.addEventListener('mousemove', mouseMoveHandler, true);
            document.addEventListener('mouseout', mouseOutHandler, true);
            document.addEventListener('click', clickHandler, true);
        }})();
        """
    def enable_selector_mode(self):
        print("ExtractorStudio Browser: Enabling selector mode.")
        self.targeting_active = True
        self.page().runJavaScript(f"window.{self.TARGETING_JS_SELECTION_VAR} = null;")
        self.page().runJavaScript(self._get_targeting_js())

    def disable_selector_mode(self):
        print("ExtractorStudio Browser: Disabling selector mode.")
        self.targeting_active = False
        cleanup_js_call = f"if (typeof window['__cleanup_' + '{self.TARGETING_JS_SELECTION_VAR}'] === 'function') {{ window['__cleanup_' + '{self.TARGETING_JS_SELECTION_VAR}'](); }}"
        self.page().runJavaScript(cleanup_js_call)
        self.page().runJavaScript(f"window.{self.TARGETING_JS_SELECTION_VAR} = null;")

    def check_for_selection(self):
        if not self.targeting_active: return
        js_to_check = f"JSON.stringify(window.{self.TARGETING_JS_SELECTION_VAR} || null);"
        def callback(result_json_str):
            if result_json_str and result_json_str != "null":
                print(f"ExtractorStudio Browser: Python received selection: {result_json_str}")
                try:
                    data = json.loads(result_json_str)
                    if data and data.get('selector'):
                        self.element_selected.emit(data['selector'], data['text'], data['type'])
                        self.targeting_active = False
                        self.page().runJavaScript(f"window.{self.TARGETING_JS_SELECTION_VAR} = null;")
                except (json.JSONDecodeError, Exception) as e:
                    print(f"ExtractorStudio Browser: Error processing selection: {e}")
        self.page().runJavaScript(js_to_check, callback)