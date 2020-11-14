CREATE or replace FUNCTION emp_stamp() RETURNS trigger AS $emp_stamp$
   BEGIN
       UPDATE stock_picking SET factura = NEW.number WHERE origin = NEW.origin;
      RETURN NULL;
   END;
$emp_stamp$ LANGUAGE plpgsql;


drop TRIGGER if EXISTS emp_stamp on account_invoice; 

CREATE TRIGGER emp_stamp after UPDATE ON account_invoice
FOR EACH ROW when (new.state = 'open') execute procedure emp_stamp()