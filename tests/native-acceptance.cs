using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class LiteSmokeNative {
  public delegate bool Callback(IntPtr hwnd,IntPtr param);
  [DllImport("user32.dll")] public static extern bool EnumWindows(Callback cb,IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent,Callback cb,IntPtr p);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint pid);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr hwnd,StringBuilder b,int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hwnd);
  [DllImport("user32.dll")] public static extern IntPtr SendMessageTimeout(IntPtr hwnd,uint msg,IntPtr w,IntPtr l,uint flags,uint timeout,out IntPtr result);
  public static IntPtr MainWindow(uint pid) {
    IntPtr result=IntPtr.Zero;
    EnumWindows((h,p)=>{uint id;GetWindowThreadProcessId(h,out id);var b=new StringBuilder(128);GetClassName(h,b,128);if(id==pid&&b.ToString()=="NppLite")result=h;return true;},IntPtr.Zero);
    return result;
  }
  public static IntPtr Editor(IntPtr parent) {
    IntPtr result=IntPtr.Zero;
    EnumChildWindows(parent,(h,p)=>{var b=new StringBuilder(128);GetClassName(h,b,128);if(b.ToString()=="Scintilla"&&IsWindowVisible(h))result=h;return true;},IntPtr.Zero);
    return result;
  }
  public static IntPtr[] Renderers(IntPtr parent) {
    var result=new List<IntPtr>();
    EnumChildWindows(parent,(h,p)=>{var b=new StringBuilder(128);GetClassName(h,b,128);if(b.ToString().StartsWith("Chrome_"))result.Add(h);return true;},IntPtr.Zero);
    return result.ToArray();
  }
  public static long Scalar(IntPtr hwnd,uint msg) {
    IntPtr result;
    if(SendMessageTimeout(hwnd,msg,IntPtr.Zero,IntPtr.Zero,2,5000,out result)==IntPtr.Zero)throw new Exception("SendMessageTimeout failed");
    return result.ToInt64();
  }
}
