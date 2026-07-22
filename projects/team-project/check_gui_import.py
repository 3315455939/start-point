import traceback
try:
    import frontend.desktop_tool_gui as gui
    print('Imported frontend.desktop_tool_gui OK')
except Exception:
    traceback.print_exc()
    print('Import FAILED')
