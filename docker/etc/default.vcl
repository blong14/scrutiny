vcl 4.0;

import directors;
import std;

backend web {
    .host = "scrutiny";
    .port = "8080";
    .probe = {
        .url = "/";
        .timeout = 60s;
        .interval = 5s;
        .window = 5;
        .threshold = 3;
    }
}

backend static {
    .host = "scrutiny-nginx";
    .port = "80";
    .probe = {
        .url = "/index.html";
        .timeout = 60s;
        .interval = 5s;
        .window = 5;
        .threshold = 3;
    }
}

sub vcl_recv {
  if (req.url ~ "(metrics)/*") {
    return (pass);
  } else if (req.url ~ "(images|static)/*") {
    set req.backend_hint = static;
    unset req.http.cookie;
    return(hash);
  } else {
    set req.backend_hint = web;
  }
}

sub vcl_hash {
  if (req.url !~ "(admin)/*" && req.http.cookie ~ "sessionid=") {
    set req.http.X-TMP = regsub(req.http.cookie, "^.*?sessionid=([^;]+);*.*$", "\1");
    hash_data(req.http.X-TMP);
    unset req.http.X-TMP;
  }
}