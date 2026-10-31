-- Exercício 1.1 — Modelagem de banco de vulnerabilidades (MySQL 8)
CREATE DATABASE IF NOT EXISTS seguranca;
USE seguranca;

DROP TABLE IF EXISTS ativo_vulnerabilidade;
DROP TABLE IF EXISTS vulnerabilidades;
DROP TABLE IF EXISTS ativos;

CREATE TABLE ativos (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    nome         VARCHAR(100) NOT NULL,
    ip           VARCHAR(45)  NOT NULL UNIQUE,
    tipo         VARCHAR(30)  NOT NULL,                 -- servidor, estacao, switch...
    criticidade  ENUM('baixa','media','alta','critica') NOT NULL DEFAULT 'media'
);

CREATE TABLE vulnerabilidades (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    cve_id      VARCHAR(20) NOT NULL UNIQUE,
    descricao   TEXT,
    severidade  ENUM('Baixa','Media','Alta','Critica') NOT NULL,
    cvss        DECIMAL(3,1) NOT NULL CHECK (cvss BETWEEN 0.0 AND 10.0)
);

-- Tabela de relacionamento N:N (um ativo tem várias vulns; uma vuln afeta vários ativos)
CREATE TABLE ativo_vulnerabilidade (
    ativo_id      INT NOT NULL,
    vuln_id       INT NOT NULL,
    status        ENUM('aberta','em_correcao','corrigida','aceita') NOT NULL DEFAULT 'aberta',
    detectada_em  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ativo_id, vuln_id),
    FOREIGN KEY (ativo_id) REFERENCES ativos(id)           ON DELETE CASCADE,
    FOREIGN KEY (vuln_id)  REFERENCES vulnerabilidades(id) ON DELETE CASCADE
);

-- Teste pedido no enunciado: SRV-WEB01 com a CVE-2024-001 (Alta, 8.5)
INSERT INTO ativos (nome, ip, tipo, criticidade) VALUES ('SRV-WEB01', '192.168.1.10', 'servidor', 'alta');
INSERT INTO vulnerabilidades (cve_id, descricao, severidade, cvss)
    VALUES ('CVE-2024-001', 'Vulnerabilidade de teste', 'Alta', 8.5);
INSERT INTO ativo_vulnerabilidade (ativo_id, vuln_id)
    SELECT a.id, v.id FROM ativos a, vulnerabilidades v
    WHERE a.nome = 'SRV-WEB01' AND v.cve_id = 'CVE-2024-001';

-- Conferência (JOIN entre as 3 tabelas)
SELECT a.nome, a.ip, v.cve_id, v.severidade, v.cvss, av.status, av.detectada_em
FROM ativo_vulnerabilidade av
JOIN ativos a           ON a.id = av.ativo_id
JOIN vulnerabilidades v ON v.id = av.vuln_id;
