# Prints volume and mute of every active audio endpoint; args "<part of device name>" <percent> set the volume.
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Collections.Generic;

[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorCom {}

[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
  int EnumAudioEndpoints(int dataFlow, int stateMask, out IMMDeviceCollection devices);
}
[Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceCollection {
  int GetCount(out int count);
  int Item(int index, out IMMDevice device);
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
  int Activate(ref Guid iid, int clsCtx, IntPtr activationParams, [MarshalAs(UnmanagedType.IUnknown)] out object iface);
  int OpenPropertyStore(int access, out IPropertyStore props);
}
[Guid("886d8eeb-8cf2-4446-8d02-cdba1dbdcf99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPropertyStore {
  int GetCount(out int count);
  int GetAt(int index, out PropertyKey key);
  int GetValue(ref PropertyKey key, out PropVariant value);
}
[StructLayout(LayoutKind.Sequential)] struct PropertyKey { public Guid fmtid; public int pid; }
[StructLayout(LayoutKind.Explicit)] struct PropVariant { [FieldOffset(0)] public short vt; [FieldOffset(8)] public IntPtr pointerValue; }

[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
  int RegisterControlChangeNotify(IntPtr p); int UnregisterControlChangeNotify(IntPtr p);
  int GetChannelCount(out int count);
  int SetMasterVolumeLevel(float level, ref Guid ctx); int SetMasterVolumeLevelScalar(float level, ref Guid ctx);
  int GetMasterVolumeLevel(out float level); int GetMasterVolumeLevelScalar(out float level);
  int SetChannelVolumeLevel(int ch, float level, ref Guid ctx); int SetChannelVolumeLevelScalar(int ch, float level, ref Guid ctx);
  int GetChannelVolumeLevel(int ch, out float level); int GetChannelVolumeLevelScalar(int ch, out float level);
  int SetMute(bool mute, ref Guid ctx); int GetMute(out bool mute);
}

public static class EndpointVolumes {
  public static List<string> Dump() {
    var res = new List<string>();
    var en = (IMMDeviceEnumerator)(new MMDeviceEnumeratorCom());
    var nameKey = new PropertyKey { fmtid = new Guid("a45c254e-df1c-4efd-8020-67d146a850e0"), pid = 14 };
    var iid = new Guid("5CDF2C82-841E-4546-9722-0CF74078229A");
    for (int flow = 0; flow <= 1; flow++) {
      IMMDeviceCollection col; en.EnumAudioEndpoints(flow, 1, out col);
      int n; col.GetCount(out n);
      for (int i = 0; i < n; i++) {
        IMMDevice dev; col.Item(i, out dev);
        IPropertyStore ps; dev.OpenPropertyStore(0, out ps);
        PropVariant pv; ps.GetValue(ref nameKey, out pv);
        string name = Marshal.PtrToStringUni(pv.pointerValue);
        object o; dev.Activate(ref iid, 23, IntPtr.Zero, out o);
        var vol = (IAudioEndpointVolume)o;
        float s; vol.GetMasterVolumeLevelScalar(out s); bool m; vol.GetMute(out m);
        res.Add(String.Format("{0,-8} {1,-44} volume {2,3:0}%  mute={3}", flow == 0 ? "OUTPUT" : "INPUT", name, s * 100, m));
      }
    }
    return res;
  }

  public static int SetByName(string part, float scalar) {
    int changed = 0;
    var en = (IMMDeviceEnumerator)(new MMDeviceEnumeratorCom());
    var nameKey = new PropertyKey { fmtid = new Guid("a45c254e-df1c-4efd-8020-67d146a850e0"), pid = 14 };
    var iid = new Guid("5CDF2C82-841E-4546-9722-0CF74078229A");
    var ctx = Guid.Empty;
    for (int flow = 0; flow <= 1; flow++) {
      IMMDeviceCollection col; en.EnumAudioEndpoints(flow, 1, out col);
      int n; col.GetCount(out n);
      for (int i = 0; i < n; i++) {
        IMMDevice dev; col.Item(i, out dev);
        IPropertyStore ps; dev.OpenPropertyStore(0, out ps);
        PropVariant pv; ps.GetValue(ref nameKey, out pv);
        string name = Marshal.PtrToStringUni(pv.pointerValue);
        if (name == null || name.IndexOf(part, StringComparison.OrdinalIgnoreCase) < 0) continue;
        object o; dev.Activate(ref iid, 23, IntPtr.Zero, out o);
        ((IAudioEndpointVolume)o).SetMasterVolumeLevelScalar(scalar, ref ctx);
        changed++;
      }
    }
    return changed;
  }
}
"@
[Console]::OutputEncoding = [Text.Encoding]::UTF8
if ($args.Count -ge 2) { "devices changed: " + [EndpointVolumes]::SetByName($args[0], [float]$args[1] / 100) }
[EndpointVolumes]::Dump() | ForEach-Object { $_ }
