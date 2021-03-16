package com.aisy.router;

import androidx.appcompat.app.AppCompatActivity;

import android.app.Activity;
import android.os.Bundle;
import android.view.Window;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

public class MainActivity extends Activity {
    @Override
public void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
     WebView webview = new WebView(this);

    setContentView(webview);
    webview.getSettings().setJavaScriptEnabled(true);
    webview.getSettings().setDomStorageEnabled(true);
    webview.loadUrl("http://10.0.2.2:5000/");

}
}