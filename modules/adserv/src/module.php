<?php
declare(strict_types=1);
return ['hooks'=>[
 'admin.menu'=>static fn()=>['label'=>'AdServ','url'=>'/admin/module-adserv.php'],
 'scheduler.tick'=>static function(){
   $q=db()->query("SELECT * FROM lxbg_mod_adserv_messages WHERE enabled=1 AND (last_sent_at IS NULL OR last_sent_at<=DATE_SUB(NOW(),INTERVAL interval_minutes MINUTE)) ORDER BY id LIMIT 25");
   $out=[];foreach($q as $r)$out[]=['id'=>(int)$r['id'],'channel'=>$r['channel_name'],'message'=>$r['message']];return $out;
 }
]];
