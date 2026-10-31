-- Exercício 1.2 — CRUD SQL completo (MySQL 8)
USE seguranca;

DROP TABLE IF EXISTS alertas;
CREATE TABLE alertas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(50), ip_origem VARCHAR(45),
    severidade ENUM('baixa','media','alta','critica'),
    status VARCHAR(20) DEFAULT 'aberto',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- (a) inserir alertas (3 pedidos + 1 extra para bater com a saída esperada do item d)
INSERT INTO alertas (tipo, ip_origem, severidade) VALUES
    ('BRUTE_FORCE', '185.220.101.1', 'critica'),
    ('PORT_SCAN',   '45.33.32.156',  'alta'),
    ('XSS',         '91.240.118.172','alta');
INSERT INTO alertas (tipo, ip_origem, severidade, criado_em) VALUES
    ('SQLI', '10.0.0.5', 'media', NOW() - INTERVAL 120 DAY);   -- alerta antigo (para o item e)

-- (b) listar apenas os de severidade 'alta'
SELECT * FROM alertas WHERE severidade = 'alta';

-- (c) atualizar um alerta para 'resolvido'
UPDATE alertas SET status = 'resolvido' WHERE id = 2;

-- (d) contar alertas por severidade
-- (ordenado da mais grave para a menos grave, como na saída esperada)
SELECT severidade, COUNT(*) AS total
FROM alertas
GROUP BY severidade
ORDER BY FIELD(severidade, 'critica', 'alta', 'media', 'baixa');
-- severidade | total
-- critica    | 1
-- alta       | 2
-- media      | 1

-- (e) apagar alertas com mais de 90 dias
DELETE FROM alertas WHERE criado_em < NOW() - INTERVAL 90 DAY;
SELECT COUNT(*) AS restantes FROM alertas;   -- 3
