vcl 4.0;

import directors;
import std;

backend static {
    .host = "static";
    .port = "80";
    .probe = {
        .url = "/index.html";
        .timeout = 1s;
        .interval = 5s;
        .window = 5;
        .threshold = 3;
    }
}

backend web {
    .host = "web";
    .port = "8080";
    .probe = {
        .url = "/";
        .timeout = 1s;
        .interval = 5s;
        .window = 5;
        .threshold = 3;
    }
}

sub vcl_recv {
    if (req.url ~ "(images|static)/*") {
        set req.backend_hint = static;
    } else {
        set req.backend_hint = web;
    }
	unset req.http.x-cache;
	return (hash);
}

sub vcl_hit {
	set req.http.x-cache = "hit";
	if (obj.ttl <= 0s && obj.grace > 0s) {
		set req.http.x-cache = "hit graced";
	}
}

sub vcl_miss {
	set req.http.x-cache = "miss";
}

sub vcl_pass {
	set req.http.x-cache = "pass";
}

sub vcl_pipe {
	set req.http.x-cache = "pipe uncacheable";
}

sub vcl_synth {
	set req.http.x-cache = "synth synth";
	# uncomment the following line to show the information in the response
	set resp.http.x-cache = req.http.x-cache;
}

sub vcl_deliver {
	if (obj.uncacheable) {
		set req.http.x-cache = req.http.x-cache + " uncacheable" ;
	} else {
		set req.http.x-cache = req.http.x-cache + " cached" ;
	}
	# uncomment the following line to show the information in the response
	set resp.http.x-cache = req.http.x-cache;
}