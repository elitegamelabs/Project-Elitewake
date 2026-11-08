// Elitewake playtest installer (owner, November 7: friends download only an exe and a README).
// GitHub limits each download to 2 GB and the game is about 3.5 GB, so the game's zip travels in two pieces: the first
// inside this exe (after the program, followed by a 32-byte trailer), the second in Elitewake-Data.bin beside it.
// Run: joins the two pieces as one stream, unpacks the game into an "Elitewake" folder next to this exe, and starts it.
// Built by Scripts/Release/make_playtest_installer.ps1 with the .NET Framework compiler that ships with Windows.
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Text;

static class Setup
{
    const string Magic = "EWSETUP1";
    const string DataName = "Elitewake-Data.bin";

    // Two byte ranges read as one seekable stream.
    sealed class Joined : Stream
    {
        readonly Stream a, b; readonly long aStart, aLen, bLen; long pos;
        public Joined(Stream a, long aStart, long aLen, Stream b, long bLen) { this.a = a; this.aStart = aStart; this.aLen = aLen; this.b = b; this.bLen = bLen; }
        public override bool CanRead { get { return true; } }
        public override bool CanSeek { get { return true; } }
        public override bool CanWrite { get { return false; } }
        public override long Length { get { return aLen + bLen; } }
        public override long Position { get { return pos; } set { pos = value; } }
        public override void Flush() { }
        public override long Seek(long offset, SeekOrigin origin)
        {
            pos = origin == SeekOrigin.Begin ? offset : origin == SeekOrigin.Current ? pos + offset : Length + offset;
            return pos;
        }
        public override void SetLength(long value) { throw new NotSupportedException(); }
        public override void Write(byte[] buffer, int offset, int count) { throw new NotSupportedException(); }
        public override int Read(byte[] buffer, int offset, int count)
        {
            if (pos >= Length) return 0;
            int n;
            if (pos < aLen)
            {
                a.Position = aStart + pos;
                n = a.Read(buffer, offset, (int)Math.Min(count, aLen - pos));
            }
            else
            {
                b.Position = pos - aLen;
                n = b.Read(buffer, offset, (int)Math.Min(count, bLen - (pos - aLen)));
            }
            pos += n;
            return n;
        }
    }

    static int Fail(string message)
    {
        Console.WriteLine();
        Console.WriteLine(message);
        Console.WriteLine("Press Enter to close.");
        Console.ReadLine();
        return 1;
    }

    static int Main()
    {
        Console.Title = "Elitewake setup";
        string exe = Process.GetCurrentProcess().MainModule.FileName;
        string here = Path.GetDirectoryName(exe);
        string target = Path.Combine(here, "Elitewake");
        string game = Path.Combine(target, "Windows", "EW.exe");
        using (FileStream self = File.OpenRead(exe))
        {
            // Trailer: payload length (8), data file length (8), build label length (8), magic (8); label just before it.
            self.Position = self.Length - 32;
            BinaryReader r = new BinaryReader(self);
            long aLen = r.ReadInt64(), bLen = r.ReadInt64(), labelLen = r.ReadInt64();
            if (Encoding.ASCII.GetString(r.ReadBytes(8)) != Magic) return Fail("This setup file is damaged. Download Elitewake-Setup.exe again.");
            self.Position = self.Length - 32 - labelLen;
            string label = Encoding.UTF8.GetString(r.ReadBytes((int)labelLen));
            long aStart = self.Length - 32 - labelLen - aLen;
            Console.WriteLine("Elitewake playtest, build " + label);
            Console.WriteLine();

            string stamp = Path.Combine(target, "build.txt");
            if (File.Exists(game) && File.Exists(stamp) && File.ReadAllText(stamp).Trim() == label)
            {
                Console.WriteLine("This build is already set up. Starting the game...");
                Process.Start(new ProcessStartInfo(game) { WorkingDirectory = Path.GetDirectoryName(game) });
                return 0;
            }
            string dataPath = Path.Combine(here, DataName);
            if (!File.Exists(dataPath))
                return Fail("Elitewake-Data.bin is missing. Download it from the same release and put it in this folder:\n" + here);
            if (new FileInfo(dataPath).Length != bLen)
                return Fail("Elitewake-Data.bin is incomplete or from another build. Download it again from the same release as this setup.");

            if (Directory.Exists(target))
            {
                Console.WriteLine("Removing the previous build in " + target + " ...");
                Directory.Delete(target, true);
            }
            Console.WriteLine("Setting up the game in " + target);
            using (FileStream data = File.OpenRead(dataPath))
            using (ZipArchive zip = new ZipArchive(new Joined(self, aStart, aLen, data, bLen), ZipArchiveMode.Read))
            {
                int done = 0, total = zip.Entries.Count, shown = -1;
                string root = Path.GetFullPath(target) + Path.DirectorySeparatorChar;
                foreach (ZipArchiveEntry entry in zip.Entries)
                {
                    string path = Path.GetFullPath(Path.Combine(target, entry.FullName));
                    if (!path.StartsWith(root, StringComparison.OrdinalIgnoreCase)) continue;      // never outside the folder
                    if (entry.FullName.EndsWith("/") || entry.FullName.EndsWith("\\")) Directory.CreateDirectory(path);
                    else
                    {
                        Directory.CreateDirectory(Path.GetDirectoryName(path));
                        entry.ExtractToFile(path, true);
                    }
                    int percent = (int)(100L * ++done / Math.Max(1, total));
                    if (percent != shown) { Console.Write("\r  " + percent + "%   "); shown = percent; }
                }
            }
            File.WriteAllText(stamp, label);
        }
        Console.WriteLine();
        if (!File.Exists(game)) return Fail("Setup finished but the game was not found at " + game);
        Console.WriteLine("Done. Starting Elitewake... (next time, Elitewake\\Windows\\EW.exe starts it directly)");
        Process.Start(new ProcessStartInfo(game) { WorkingDirectory = Path.GetDirectoryName(game) });
        return 0;
    }
}
