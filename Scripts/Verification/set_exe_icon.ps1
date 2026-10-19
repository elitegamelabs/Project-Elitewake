<# Replace the icon of a Windows executable (or SFX module) with a .ico file, in place, using the Windows resource
API: every existing icon group is removed, then the .ico's images are written as icon group 1. Use it on copies;
the packer stamps the self-extractor module this way (owner, October 19: the EW icon with a silver box).
-AsInvoker also gives it a manifest that runs it with the user's own rights: the 7-Zip self-extractor has none and
describes itself as a setup program, so Windows' installer detection otherwise demands an administrator prompt. #>
param([Parameter(Mandatory=$true)][string]$Executable, [Parameter(Mandatory=$true)][string]$Icon, [switch]$AsInvoker)
$ErrorActionPreference='Stop'
if (-not ('EwIconRes' -as [type])) {
Add-Type @'
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
public static class EwIconRes {
    delegate bool EnumNames(IntPtr module, IntPtr type, IntPtr name, IntPtr param);
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)] static extern IntPtr LoadLibraryEx(string path, IntPtr file, uint flags);
    [DllImport("kernel32.dll")] static extern bool FreeLibrary(IntPtr module);
    [DllImport("kernel32.dll")] static extern bool EnumResourceNames(IntPtr module, IntPtr type, EnumNames cb, IntPtr param);
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)] static extern IntPtr BeginUpdateResource(string path, bool deleteAll);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool UpdateResource(IntPtr update, IntPtr type, IntPtr name, ushort lang, byte[] data, uint size);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool EndUpdateResource(IntPtr update, bool discard);
    [DllImport("kernel32.dll")] static extern IntPtr FindResourceEx(IntPtr module, IntPtr type, IntPtr name, ushort lang);
    delegate bool EnumLangs(IntPtr module, IntPtr type, IntPtr name, ushort lang, IntPtr param);
    [DllImport("kernel32.dll")] static extern bool EnumResourceLanguages(IntPtr module, IntPtr type, IntPtr name, EnumLangs cb, IntPtr param);
    const int RT_ICON = 3, RT_GROUP_ICON = 14;

    // (type, integer id, language) of every icon and icon group in the file; named resources are reported as -1.
    public static List<int[]> List(string path) {
        var found = new List<int[]>();
        IntPtr m = LoadLibraryEx(path, IntPtr.Zero, 0x2);   // LOAD_LIBRARY_AS_DATAFILE
        if (m == IntPtr.Zero) throw new IOException("cannot open " + path);
        try {
            foreach (int t in new[] { RT_GROUP_ICON, RT_ICON }) {
                EnumResourceNames(m, (IntPtr)t, (mod, ty, name, p) => {
                    long id = name.ToInt64();
                    if (id >> 16 != 0) throw new InvalidOperationException("named icon resources are not handled");
                    EnumResourceLanguages(mod, ty, name, (m2, t2, n2, lang, p2) => { found.Add(new[] { t, (int)id, lang }); return true; }, IntPtr.Zero);
                    return true;
                }, IntPtr.Zero);
            }
        } finally { FreeLibrary(m); }
        return found;
    }

    public static void SetManifest(string path, string xml) {
        byte[] b = System.Text.Encoding.UTF8.GetBytes(xml);
        IntPtr u = BeginUpdateResource(path, false);
        if (u == IntPtr.Zero) throw new IOException("BeginUpdateResource failed " + Marshal.GetLastWin32Error());
        bool ok = UpdateResource(u, (IntPtr)24, (IntPtr)1, 1033, b, (uint)b.Length);   // RT_MANIFEST, CREATEPROCESS_MANIFEST_RESOURCE_ID
        if (!EndUpdateResource(u, !ok) || !ok) throw new IOException("manifest failed " + Marshal.GetLastWin32Error());
    }

    public static string Replace(string path, string ico) {
        var old = List(path);
        byte[] f = File.ReadAllBytes(ico);
        int count = BitConverter.ToUInt16(f, 4);
        IntPtr u = BeginUpdateResource(path, false);
        if (u == IntPtr.Zero) throw new IOException("BeginUpdateResource failed " + Marshal.GetLastWin32Error());
        bool ok = false;
        try {
            foreach (var r in old)
                if (!UpdateResource(u, (IntPtr)r[0], (IntPtr)r[1], (ushort)r[2], null, 0)) throw new IOException("delete failed " + Marshal.GetLastWin32Error());
            var group = new MemoryStream();
            var w = new BinaryWriter(group);
            w.Write((ushort)0); w.Write((ushort)1); w.Write((ushort)count);
            for (int i = 0; i < count; i++) {
                int e = 6 + 16 * i;
                int bytes = BitConverter.ToInt32(f, e + 8), offset = BitConverter.ToInt32(f, e + 12);
                byte[] image = new byte[bytes];
                Array.Copy(f, offset, image, 0, bytes);
                ushort id = (ushort)(100 + i);
                if (!UpdateResource(u, (IntPtr)RT_ICON, (IntPtr)id, 1033, image, (uint)bytes)) throw new IOException("icon failed " + Marshal.GetLastWin32Error());
                w.Write(f, e, 8);            // width, height, colours, reserved, planes, bit count
                w.Write(bytes); w.Write(id);
            }
            byte[] g = group.ToArray();
            if (!UpdateResource(u, (IntPtr)RT_GROUP_ICON, (IntPtr)1, 1033, g, (uint)g.Length)) throw new IOException("group failed " + Marshal.GetLastWin32Error());
            ok = true;
        } finally {
            if (!EndUpdateResource(u, !ok)) throw new IOException("EndUpdateResource failed " + Marshal.GetLastWin32Error());
        }
        return "removed " + old.Count + " icon resources, wrote " + count + " images";
    }
}
'@
}
$exe = (Resolve-Path -LiteralPath $Executable).Path
$ico = (Resolve-Path -LiteralPath $Icon).Path
[EwIconRes]::Replace($exe, $ico)
if ($AsInvoker) {
    [EwIconRes]::SetManifest($exe, @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security><requestedPrivileges><requestedExecutionLevel level="asInvoker" uiAccess="false"/></requestedPrivileges></security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application><supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/></application>
  </compatibility>
</assembly>
'@)
    'manifest: runs as invoker'
}
$after = [EwIconRes]::List($exe)
if (-not ($after | Where-Object { $_[0] -eq 14 -and $_[1] -eq 1 })) { throw 'The new icon group is missing.' }
