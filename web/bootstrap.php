<?php
declare(strict_types=1);
session_name('lxbg_services_ce');
session_set_cookie_params(['httponly'=>true,'secure'=>true,'samesite'=>'Lax']);
session_start();
$cfgPath = getenv('LXBG_WEB_CONFIG') ?: dirname(__DIR__).'/config.json';
$raw = @file_get_contents($cfgPath);
$config = $raw ? (json_decode($raw,true) ?: []) : [];
if (empty($config['db'])) { http_response_code(500); exit('LXBG configuration missing.'); }
function db(): PDO { static $pdo; global $config; if (!$pdo) {$d=$config['db'];$pdo=new PDO("mysql:host={$d['host']};port={$d['port']};dbname={$d['database']};charset=utf8mb4",$d['username'],$d['password'],[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC]);} return $pdo; }
function e(string $s): string { return htmlspecialchars($s,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8'); }
function csrf(): string { if(empty($_SESSION['csrf'])) $_SESSION['csrf']=bin2hex(random_bytes(32)); return $_SESSION['csrf']; }
function csrf_check(): void { if(!hash_equals($_SESSION['csrf']??'',(string)($_POST['csrf']??''))) {http_response_code(419);exit('Ungültige Sitzung. Bitte Seite neu laden.');} }
function user(): ?array { if(empty($_SESSION['uid'])) return null; $q=db()->prepare("SELECT id,username,email,role FROM ls_users WHERE id=? AND status='active'");$q->execute([(int)$_SESSION['uid']]);return $q->fetch()?:null; }
function need_user(): array { $u=user(); if(!$u){header('Location: login.php');exit;} return $u; }
function norm_nick(string $s): string { return mb_strtolower(trim($s),'UTF-8'); }
function valid_nick(string $s): bool { return (bool)preg_match('/^[A-Za-z][A-Za-z0-9_\-\[\]\\`^{}|]{1,30}$/D',$s); }
function valid_channel(string $s): bool { return (bool)preg_match('/^#[^\x00\x07\x0A\x0D ,:]{1,62}$/D',$s); }
