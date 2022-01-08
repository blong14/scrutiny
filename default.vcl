vcl 4.0;

import directors;
import std;

backend web1 {
    .host = "web1";
    .port = "8080";
    .probe = {
        .url = "/";
        .timeout = 1s;
        .interval = 5s;
        .window = 5;
        .threshold = 3;
    }
}

backend web2 {
    .host = "web2";
    .port = "8080";
    .probe = {
        .url = "/";
        .timeout = 1s;
        .interval = 5s;
        .window = 5;
        .threshold = 3;
    }
}

sub vcl_init {
    new balancer = directors.round_robin();
    balancer.add_backend(web1);
    balancer.add_backend(web2);
}

sub vcl_recv {
    set req.backend_hint = balancer.backend();
	unset req.http.x-cache;
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