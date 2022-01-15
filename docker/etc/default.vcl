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
  } else {
    set req.backend_hint = web;
  }
}

